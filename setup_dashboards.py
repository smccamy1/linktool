#!/usr/bin/env python3
"""
OpenSearch Dashboards Setup Script
Creates index patterns, visualizations, and dashboards for IDV data.
"""

import requests
import json
from datetime import datetime

# OpenSearch Dashboards configuration
DASHBOARDS_URL = "http://localhost:5601"
OPENSEARCH_URL = "http://localhost:9200"

def create_index_pattern():
    """Create index pattern for idv_verifications."""
    print("Creating index pattern...")
    
    index_pattern = {
        "attributes": {
            "title": "idv_verifications*",
            "timeFieldName": "submittedAt"
        }
    }
    
    response = requests.post(
        f"{DASHBOARDS_URL}/api/saved_objects/index-pattern/idv_verifications",
        headers={"osd-xsrf": "true", "Content-Type": "application/json"},
        json=index_pattern
    )
    
    if response.status_code in [200, 409]:  # 409 means it already exists
        print("✓ Index pattern created/exists")
        return True
    else:
        print(f"Error creating index pattern: {response.status_code}")
        print(response.text)
        return False

def create_visualization(vis_id, vis_config):
    """Create a visualization in OpenSearch Dashboards."""
    response = requests.post(
        f"{DASHBOARDS_URL}/api/saved_objects/visualization/{vis_id}",
        headers={"osd-xsrf": "true", "Content-Type": "application/json"},
        json=vis_config
    )
    
    if response.status_code in [200, 409]:
        return True
    else:
        print(f"Error creating visualization {vis_id}: {response.status_code}")
        return False

def create_visualizations():
    """Create sample visualizations."""
    print("\nCreating visualizations...")
    
    # 1. Verification Status Pie Chart
    status_pie = {
        "attributes": {
            "title": "Verification Status Distribution",
            "visState": json.dumps({
                "title": "Verification Status Distribution",
                "type": "pie",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "terms",
                        "schema": "segment",
                        "params": {
                            "field": "status",
                            "size": 10,
                            "order": "desc",
                            "orderBy": "1"
                        }
                    }
                ],
                "params": {
                    "type": "pie",
                    "addTooltip": True,
                    "addLegend": True,
                    "legendPosition": "right",
                    "isDonut": True
                }
            }),
            "uiStateJSON": "{}",
            "description": "Distribution of verification statuses",
            "version": 1,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "index": "idv_verifications",
                    "query": {"query": "", "language": "lucene"},
                    "filter": []
                })
            }
        }
    }
    
    # 2. Risk Level Bar Chart
    risk_bar = {
        "attributes": {
            "title": "Risk Level Distribution",
            "visState": json.dumps({
                "title": "Risk Level Distribution",
                "type": "histogram",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "terms",
                        "schema": "segment",
                        "params": {
                            "field": "riskLevel",
                            "size": 5,
                            "order": "desc",
                            "orderBy": "1"
                        }
                    }
                ],
                "params": {
                    "type": "histogram",
                    "grid": {"categoryLines": False},
                    "categoryAxes": [{
                        "id": "CategoryAxis-1",
                        "type": "category",
                        "position": "bottom",
                        "show": True,
                        "style": {},
                        "scale": {"type": "linear"},
                        "labels": {"show": True, "filter": True, "truncate": 100},
                        "title": {}
                    }],
                    "valueAxes": [{
                        "id": "ValueAxis-1",
                        "name": "LeftAxis-1",
                        "type": "value",
                        "position": "left",
                        "show": True,
                        "style": {},
                        "scale": {"type": "linear", "mode": "normal"},
                        "labels": {"show": True, "rotate": 0, "filter": False, "truncate": 100},
                        "title": {"text": "Count"}
                    }],
                    "seriesParams": [{
                        "show": True,
                        "type": "histogram",
                        "mode": "stacked",
                        "data": {"label": "Count", "id": "1"},
                        "valueAxis": "ValueAxis-1",
                        "drawLinesBetweenPoints": True,
                        "lineWidth": 2,
                        "showCircles": True
                    }],
                    "addTooltip": True,
                    "addLegend": True,
                    "legendPosition": "right",
                    "times": [],
                    "addTimeMarker": False
                }
            }),
            "uiStateJSON": "{}",
            "description": "Count of verifications by risk level",
            "version": 1,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "index": "idv_verifications",
                    "query": {"query": "", "language": "lucene"},
                    "filter": []
                })
            }
        }
    }
    
    # 3. Verification Timeline
    timeline = {
        "attributes": {
            "title": "Verifications Over Time",
            "visState": json.dumps({
                "title": "Verifications Over Time",
                "type": "line",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "date_histogram",
                        "schema": "segment",
                        "params": {
                            "field": "submittedAt",
                            "interval": "auto",
                            "min_doc_count": 1
                        }
                    }
                ],
                "params": {
                    "type": "line",
                    "grid": {"categoryLines": False},
                    "categoryAxes": [{
                        "id": "CategoryAxis-1",
                        "type": "category",
                        "position": "bottom",
                        "show": True,
                        "style": {},
                        "scale": {"type": "linear"},
                        "labels": {"show": True, "filter": True, "truncate": 100},
                        "title": {}
                    }],
                    "valueAxes": [{
                        "id": "ValueAxis-1",
                        "name": "LeftAxis-1",
                        "type": "value",
                        "position": "left",
                        "show": True,
                        "style": {},
                        "scale": {"type": "linear", "mode": "normal"},
                        "labels": {"show": True, "rotate": 0, "filter": False, "truncate": 100},
                        "title": {"text": "Count"}
                    }],
                    "seriesParams": [{
                        "show": True,
                        "type": "line",
                        "mode": "normal",
                        "data": {"label": "Count", "id": "1"},
                        "valueAxis": "ValueAxis-1",
                        "drawLinesBetweenPoints": True,
                        "lineWidth": 2,
                        "showCircles": True
                    }],
                    "addTooltip": True,
                    "addLegend": True,
                    "legendPosition": "right",
                    "times": [],
                    "addTimeMarker": False
                }
            }),
            "uiStateJSON": "{}",
            "description": "Timeline of verification submissions",
            "version": 1,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "index": "idv_verifications",
                    "query": {"query": "", "language": "lucene"},
                    "filter": []
                })
            }
        }
    }
    
    # 4. Document Type Distribution
    doc_type_pie = {
        "attributes": {
            "title": "Document Type Distribution",
            "visState": json.dumps({
                "title": "Document Type Distribution",
                "type": "pie",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "terms",
                        "schema": "segment",
                        "params": {
                            "field": "documentType",
                            "size": 10,
                            "order": "desc",
                            "orderBy": "1"
                        }
                    }
                ],
                "params": {
                    "type": "pie",
                    "addTooltip": True,
                    "addLegend": True,
                    "legendPosition": "right",
                    "isDonut": False
                }
            }),
            "uiStateJSON": "{}",
            "description": "Distribution of document types used for verification",
            "version": 1,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "index": "idv_verifications",
                    "query": {"query": "", "language": "lucene"},
                    "filter": []
                })
            }
        }
    }
    
    # 5. Confidence Score Metric
    confidence_metric = {
        "attributes": {
            "title": "Average Confidence Score",
            "visState": json.dumps({
                "title": "Average Confidence Score",
                "type": "metric",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "avg",
                        "schema": "metric",
                        "params": {
                            "field": "confidence_score"
                        }
                    }
                ],
                "params": {
                    "addTooltip": True,
                    "addLegend": False,
                    "type": "metric",
                    "metric": {
                        "percentageMode": False,
                        "useRanges": False,
                        "colorSchema": "Green to Red",
                        "metricColorMode": "None",
                        "colorsRange": [{"from": 0, "to": 10000}],
                        "labels": {"show": True},
                        "invertColors": False,
                        "style": {
                            "bgFill": "#000",
                            "bgColor": False,
                            "labelColor": False,
                            "subText": "",
                            "fontSize": 60
                        }
                    }
                }
            }),
            "uiStateJSON": "{}",
            "description": "Average confidence score across all verifications",
            "version": 1,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "index": "idv_verifications",
                    "query": {"query": "", "language": "lucene"},
                    "filter": []
                })
            }
        }
    }
    
    visualizations = {
        "status-pie": status_pie,
        "risk-bar": risk_bar,
        "timeline": timeline,
        "doc-type-pie": doc_type_pie,
        "confidence-metric": confidence_metric
    }
    
    for vis_id, vis_config in visualizations.items():
        if create_visualization(vis_id, vis_config):
            print(f"✓ Created visualization: {vis_config['attributes']['title']}")
        else:
            print(f"✗ Failed to create visualization: {vis_id}")

def create_dashboard():
    """Create main IDV dashboard."""
    print("\nCreating dashboard...")
    
    dashboard = {
        "attributes": {
            "title": "IDV Analytics Dashboard",
            "hits": 0,
            "description": "Identity Verification analytics and monitoring",
            "panelsJSON": json.dumps([
                {
                    "version": "2.11.1",
                    "gridData": {"x": 0, "y": 0, "w": 24, "h": 15, "i": "1"},
                    "panelIndex": "1",
                    "embeddableConfig": {},
                    "panelRefName": "panel_1"
                },
                {
                    "version": "2.11.1",
                    "gridData": {"x": 24, "y": 0, "w": 24, "h": 15, "i": "2"},
                    "panelIndex": "2",
                    "embeddableConfig": {},
                    "panelRefName": "panel_2"
                },
                {
                    "version": "2.11.1",
                    "gridData": {"x": 0, "y": 15, "w": 48, "h": 15, "i": "3"},
                    "panelIndex": "3",
                    "embeddableConfig": {},
                    "panelRefName": "panel_3"
                },
                {
                    "version": "2.11.1",
                    "gridData": {"x": 0, "y": 30, "w": 24, "h": 15, "i": "4"},
                    "panelIndex": "4",
                    "embeddableConfig": {},
                    "panelRefName": "panel_4"
                },
                {
                    "version": "2.11.1",
                    "gridData": {"x": 24, "y": 30, "w": 24, "h": 15, "i": "5"},
                    "panelIndex": "5",
                    "embeddableConfig": {},
                    "panelRefName": "panel_5"
                }
            ]),
            "optionsJSON": json.dumps({
                "useMargins": True,
                "hidePanelTitles": False
            }),
            "version": 1,
            "timeRestore": False,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "query": {"query": "", "language": "lucene"},
                    "filter": []
                })
            }
        },
        "references": [
            {"name": "panel_1", "type": "visualization", "id": "status-pie"},
            {"name": "panel_2", "type": "visualization", "id": "risk-bar"},
            {"name": "panel_3", "type": "visualization", "id": "timeline"},
            {"name": "panel_4", "type": "visualization", "id": "doc-type-pie"},
            {"name": "panel_5", "type": "visualization", "id": "confidence-metric"}
        ]
    }
    
    response = requests.post(
        f"{DASHBOARDS_URL}/api/saved_objects/dashboard/idv-dashboard",
        headers={"osd-xsrf": "true", "Content-Type": "application/json"},
        json=dashboard
    )
    
    if response.status_code in [200, 409]:
        print("✓ Dashboard created successfully")
        print(f"\nAccess your dashboard at: {DASHBOARDS_URL}/app/dashboards#/view/idv-dashboard")
        return True
    else:
        print(f"Error creating dashboard: {response.status_code}")
        print(response.text)
        return False

def main():
    print("=" * 60)
    print("OpenSearch Dashboards Setup")
    print("=" * 60)
    
    # Check if OpenSearch is accessible
    try:
        response = requests.get(OPENSEARCH_URL)
        print(f"✓ OpenSearch is accessible at {OPENSEARCH_URL}")
    except Exception as e:
        print(f"✗ Cannot connect to OpenSearch: {e}")
        return
    
    # Check if Dashboards is accessible
    try:
        response = requests.get(DASHBOARDS_URL)
        print(f"✓ OpenSearch Dashboards is accessible at {DASHBOARDS_URL}")
    except Exception as e:
        print(f"✗ Cannot connect to OpenSearch Dashboards: {e}")
        return
    
    print()
    
    # Create index pattern
    if not create_index_pattern():
        print("Failed to create index pattern. Exiting.")
        return
    
    # Create visualizations
    create_visualizations()
    
    # Create dashboard
    create_dashboard()
    
    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print(f"\nOpen OpenSearch Dashboards: {DASHBOARDS_URL}")
    print("Navigate to Dashboards → IDV Analytics Dashboard")
    print()

if __name__ == "__main__":
    main()
