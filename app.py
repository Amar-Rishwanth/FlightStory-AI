import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard import load_project_data, filter_events, filter_incidents, summarize_incident
from src.timeline import build_incident_timeline


st.set_page_config(page_title="FlightStory AI", page_icon="✈️", layout="wide")

st.title("FlightStory AI")
st.caption("AI-Assisted Multi-System Log Analysis & Incident Visualization")
st.caption("Development POC using synthetic flight-management log data.")


@st.cache_data
def _load_data():
    return load_project_data()


def _incident_rows(incidents):
    rows = []
    for incident in incidents:
        timeline = build_incident_timeline(incident)
        rows.append(
            {
                "Incident ID": incident.incident_id,
                "Start": incident.start_time.isoformat(),
                "End": incident.end_time.isoformat(),
                "Duration": f"{incident.duration_seconds:.0f}s",
                "Nodes": ", ".join(incident.nodes),
                "Event count": len(incident.events),
                "Fault count": len(timeline.fault_events),
                "Recovery status": "present" if timeline.recovery_events else "none",
                "Confidence": f"{incident.confidence:.2f}",
            }
        )
    return rows


def main():
    events, incidents, report, skipped = _load_data()

    if not events:
        st.warning("No dataset events were loaded. Check the CSV files under the data directory.")
        return

    min_time = min(event.timestamp for event in events)
    max_time = max(event.timestamp for event in events)

    with st.sidebar:
        st.header("Filters")

        node_filter = st.selectbox("Node", ["All"] + sorted({event.node for event in events}))
        log_family_filter = st.selectbox("Log family", ["All"] + sorted({event.log_family for event in events}))
        category_filter = st.selectbox("Category", ["All"] + sorted({str(event.category or "") for event in events if event.category}))

        time_start = st.slider("Start time", min_value=min_time, max_value=max_time, value=min_time)
        time_end = st.slider("End time", min_value=min_time, max_value=max_time, value=max_time)
        if time_start > time_end:
            time_start, time_end = time_end, time_start

        incident_filter = st.selectbox(
            "Incident",
            ["All"] + [incident.incident_id for incident in incidents],
        )

    filtered_events = filter_events(
        events,
        node=node_filter,
        start=time_start,
        end=time_end,
        log_family=log_family_filter,
        category=category_filter,
    )
    filtered_incidents = filter_incidents(
        incidents,
        node=node_filter,
        start=time_start,
        end=time_end,
        log_family=log_family_filter,
        category=category_filter,
        incident_id=incident_filter,
    )

    if not filtered_events:
        st.info("No events match the current filters.")
        return

    if not filtered_incidents:
        st.info("No incidents match the current filters.")
        return

    st.subheader("Level 1 — Incident Overview")
    total_log_records = len(events)
    normalized_events = len(filtered_events)
    incident_count = len(filtered_incidents)
    fault_count = sum(
        1 for event in filtered_events if event.log_family == "faults_recovery" or "fault" in str(event.category or "").lower()
    )
    nodes_involved = sorted({event.node for event in filtered_events})

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total log records", total_log_records)
    col2.metric("Normalized events", normalized_events)
    col3.metric("Incidents", incident_count)
    col4.metric("Fault events", fault_count)
    col5.metric("Nodes involved", len(nodes_involved))

    incident_df = pd.DataFrame(_incident_rows(filtered_incidents))
    if incident_df.empty:
        st.warning("No incident data available for the active filters.")
        return

    st.dataframe(incident_df, use_container_width=True, hide_index=True)

    selected_incident_id = st.selectbox(
        "Select incident",
        [incident.incident_id for incident in filtered_incidents],
        index=0,
    )
    selected_incident = next(incident for incident in filtered_incidents if incident.incident_id == selected_incident_id)
    selected_timeline = build_incident_timeline(selected_incident)

    st.subheader(f"Level 2 — Incident / Fault Detail: {selected_incident_id}")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Start", selected_incident.start_time.isoformat())
    c2.metric("End", selected_incident.end_time.isoformat())
    c3.metric("Duration", f"{selected_incident.duration_seconds:.0f}s")
    c4.metric("Affected nodes", ", ".join(selected_incident.nodes))
    c5.metric("Confidence", f"{selected_incident.confidence:.2f}")

    event_rows = []
    for event in selected_incident.events:
        event_rows.append(
            {
                "Timestamp": event.timestamp.isoformat(),
                "Node": event.node,
                "Event type": event.event_type,
                "Category": event.category,
                "Code": event.code,
                "Severity": event.severity,
                "Message": event.message,
                "Evidence ID": event.evidence_id,
                "Log family": event.log_family,
            }
        )

    st.dataframe(pd.DataFrame(event_rows), use_container_width=True, hide_index=True)

    st.subheader("Incident Story Summary")
    st.write(summarize_incident(selected_incident))

    st.subheader("Level 3 — Operation Context")
    context_df = pd.DataFrame(
        [
            {
                "timestamp": event.timestamp,
                "node": event.node,
                "event_type": event.event_type,
                "category": event.category,
                "severity": event.severity,
                "evidence_id": event.evidence_id,
                "log_family": event.log_family,
            }
            for event in selected_incident.events
        ]
    )
    if not context_df.empty:
        fig = px.scatter(
            context_df,
            x="timestamp",
            y="node",
            color="log_family",
            hover_name="event_type",
            hover_data={
                "timestamp": True,
                "node": True,
                "event_type": True,
                "category": True,
                "severity": True,
                "evidence_id": True,
            },
            category_orders={"node": sorted({row["node"] for _, row in context_df.iterrows()})},
        )
        fig.update_traces(marker=dict(size=10))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(context_df.sort_values("timestamp")[["timestamp", "node", "event_type", "category", "severity", "evidence_id"]], use_container_width=True, hide_index=True)

    st.subheader("Level 4 — Evidence Detail")
    evidence_options = [event.evidence_id for event in selected_incident.events]
    evidence_choice = st.selectbox("Select evidence", evidence_options, index=0 if evidence_options else None)

    if evidence_choice:
        selected_event = next(event for event in selected_incident.events if event.evidence_id == evidence_choice)
        st.subheader(f"Evidence ID: {selected_event.evidence_id}")
        st.json(
            {
                "Evidence ID": selected_event.evidence_id,
                "Event ID": selected_event.event_id,
                "Source file": selected_event.source_file,
                "Source row": selected_event.source_row,
                "Timestamp": selected_event.timestamp.isoformat(),
                "Node": selected_event.node,
                "Log family": selected_event.log_family,
                "Event type": selected_event.event_type,
                "Category": selected_event.category,
                "Code": selected_event.code,
                "Severity": selected_event.severity,
                "Message": selected_event.message,
                "Raw record": selected_event.raw_record,
            }
        )


if __name__ == "__main__":
    main()
