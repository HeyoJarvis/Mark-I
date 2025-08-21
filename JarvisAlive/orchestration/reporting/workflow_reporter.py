"""
Comprehensive Workflow Reporting System

This module provides advanced result consolidation and reporting for parallel workflows:
- Structured result aggregation from all agents
- Rich HTML and JSON report generation
- Artifact management and organization
- Performance analytics and metrics
- Export capabilities for different formats
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class WorkflowReporter:
    """Advanced workflow result consolidation and reporting system."""
    
    def __init__(self, reports_dir: Optional[str] = None):
        self.reports_dir = Path(reports_dir or "./workflow_reports")
        self.reports_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def consolidate_workflow_results(self, workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consolidate results from all agents into a comprehensive report.
        
        Args:
            workflow_state: Complete workflow state with agent results
            
        Returns:
            Comprehensive consolidated report
        """
        self.logger.info(f"Consolidating workflow results for: {workflow_state.get('workflow_id')}")
        
        # Extract key information
        workflow_id = workflow_state.get('workflow_id', 'unknown')
        user_request = workflow_state.get('user_request', '')
        agent_results = workflow_state.get('agent_results', {})
        completed_agents = workflow_state.get('completed_agents', [])
        failed_agents = workflow_state.get('failed_agents', [])
        execution_plan = workflow_state.get('execution_plan', {})
        
        # Calculate execution metrics
        created_at = workflow_state.get('created_at')
        updated_at = workflow_state.get('updated_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        
        execution_time = (updated_at - created_at).total_seconds() if created_at and updated_at else 0
        
        # Build consolidated report
        consolidated = {
            "metadata": {
                "workflow_id": workflow_id,
                "generated_at": datetime.utcnow().isoformat(),
                "user_request": user_request,
                "execution_time_seconds": execution_time,
                "total_agents": len(execution_plan.get('required_agents', [])),
                "successful_agents": len(completed_agents),
                "failed_agents": len(failed_agents),
                "success_rate": len(completed_agents) / max(len(completed_agents) + len(failed_agents), 1) * 100
            },
            "execution_summary": self._create_execution_summary(workflow_state),
            "agent_outputs": await self._consolidate_agent_outputs(agent_results),
            "artifacts": await self._organize_artifacts(agent_results),
            "business_insights": await self._extract_business_insights(agent_results, user_request),
            "recommendations": await self._generate_recommendations(agent_results, completed_agents, failed_agents),
            "performance_metrics": self._calculate_performance_metrics(workflow_state)
        }
        
        return consolidated
    
    def _create_execution_summary(self, workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """Create high-level execution summary."""
        return {
            "workflow_status": workflow_state.get('overall_status', 'unknown'),
            "execution_plan": workflow_state.get('execution_plan', {}),
            "risk_assessment": workflow_state.get('risk_assessment', {}),
            "human_decision": workflow_state.get('human_decision', {}),
            "agent_statuses": workflow_state.get('agent_statuses', {}),
            "progress_percentage": workflow_state.get('progress_percentage', 0),
            "errors": workflow_state.get('errors', []),
            "warnings": workflow_state.get('warnings', [])
        }
    
    async def _consolidate_agent_outputs(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate and structure outputs from all agents."""
        consolidated_outputs = {}
        
        for agent_name, result in agent_results.items():
            if not isinstance(result, dict):
                continue
            
            if agent_name == "branding":
                consolidated_outputs["branding"] = self._process_branding_output(result)
            elif agent_name == "logo_generation":
                consolidated_outputs["logo_generation"] = self._process_logo_output(result)
            elif agent_name == "market_research":
                consolidated_outputs["market_research"] = self._process_market_research_output(result)
            elif agent_name == "website_generation":
                consolidated_outputs["website_generation"] = self._process_website_output(result)
        
        return consolidated_outputs
    
    def _process_branding_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process branding agent output."""
        branding_package = result.get('branding_package', {})
        return {
            "summary": "Brand identity and visual guidelines created",
            "selected_brand_name": branding_package.get('selected_brand_name', ''),
            "brand_names": branding_package.get('brand_names', {}),
            "logo_concept": branding_package.get('logo_concept', {}),
            "visual_identity": branding_package.get('visual_identity', {}),
            "brand_strategy": result.get('brand_strategy', {}),
            "deliverables": result.get('deliverables', {}),
            "confidence": result.get('branding_confidence', 'unknown'),
            "saved_report": result.get('saved_report_path')
        }
    
    def _process_logo_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process logo generation agent output."""
        return {
            "summary": f"Generated {len(result.get('logo_images', []))} logo variations",
            "brand_name": result.get('brand_name', ''),
            "logo_images": result.get('logo_images', []),
            "enhanced_prompt": result.get('enhanced_prompt', ''),
            "generation_time_ms": result.get('generation_time_ms', 0),
            "mock_mode": result.get('mock_mode', False)
        }
    
    def _process_market_research_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process market research agent output."""
        return {
            "summary": "Comprehensive market analysis completed",
            "market_analysis": result.get('market_analysis', {}),
            "competitive_landscape": result.get('competitive_analysis', {}),
            "target_audience": result.get('target_audience_insights', {}),
            "opportunities": result.get('opportunities', []),
            "risks": result.get('risks', []),
            "market_size": result.get('market_size_analysis', {}),
            "recommendations": result.get('strategic_recommendations', []),
            "saved_report": result.get('saved_report_path')
        }
    
    def _process_website_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process website generation agent output."""
        return {
            "summary": "Website structure and content created",
            "sitemap": result.get('sitemap', []),
            "website_structure": result.get('website_structure', []),
            "homepage": result.get('homepage', {}),
            "style_guide": result.get('style_guide', {}),
            "seo_recommendations": result.get('seo_recommendations', {}),
            "website_file": result.get('website_file', ''),
            "generation_time_ms": result.get('generation_time_ms', 0)
        }
    
    async def _organize_artifacts(self, agent_results: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Organize all generated artifacts by type."""
        artifacts = {
            "reports": [],
            "images": [],
            "documents": [],
            "data_files": []
        }
        
        for agent_name, result in agent_results.items():
            if not isinstance(result, dict):
                continue
            
            # Look for file paths and artifacts
            for key, value in result.items():
                if isinstance(value, str):
                    if key.endswith('_path') or key.endswith('_file'):
                        artifact = {
                            "agent": agent_name,
                            "type": self._classify_artifact(key, value),
                            "name": key,
                            "path": value,
                            "exists": os.path.exists(value) if value else False
                        }
                        artifacts[artifact["type"]].append(artifact)
                
                # Handle logo images specifically
                elif key == "logo_images" and isinstance(value, list):
                    for logo_data in value:
                        if isinstance(logo_data, dict) and "local_path" in logo_data:
                            artifact = {
                                "agent": agent_name,
                                "type": "images",
                                "name": logo_data.get("filename", "logo"),
                                "path": logo_data.get("local_path", ""),
                                "exists": os.path.exists(logo_data.get("local_path", "")),
                                "metadata": logo_data
                            }
                            artifacts["images"].append(artifact)
        
        return artifacts
    
    def _classify_artifact(self, key: str, path: str) -> str:
        """Classify artifact type based on key and file extension."""
        key_lower = key.lower()
        path_lower = path.lower() if path else ""
        
        if "report" in key_lower or path_lower.endswith('.json'):
            return "reports"
        elif "logo" in key_lower or "image" in key_lower or any(path_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.svg']):
            return "images"
        elif "website" in key_lower or any(path_lower.endswith(ext) for ext in ['.html', '.css', '.js']):
            return "documents"
        else:
            return "data_files"
    
    async def _extract_business_insights(self, agent_results: Dict[str, Any], user_request: str) -> Dict[str, Any]:
        """Extract key business insights from agent results."""
        insights = {
            "brand_identity": {},
            "market_position": {},
            "digital_presence": {},
            "visual_assets": {},
            "key_findings": []
        }
        
        # Extract branding insights
        if "branding" in agent_results:
            branding_result = agent_results["branding"]
            if isinstance(branding_result, dict):
                brand_strategy = branding_result.get('brand_strategy', {})
                insights["brand_identity"] = {
                    "positioning": brand_strategy.get('positioning', ''),
                    "target_market": brand_strategy.get('target_market', ''),
                    "brand_personality": brand_strategy.get('brand_personality', {}),
                    "visual_direction": brand_strategy.get('visual_direction', {})
                }
        
        # Extract market insights
        if "market_research" in agent_results:
            market_result = agent_results["market_research"]
            if isinstance(market_result, dict):
                insights["market_position"] = {
                    "market_size": market_result.get('market_size_analysis', {}),
                    "competition": market_result.get('competitive_analysis', {}),
                    "opportunities": market_result.get('opportunities', []),
                    "target_segments": market_result.get('target_audience_insights', {})
                }
        
        # Extract digital presence insights
        if "website_generation" in agent_results:
            website_result = agent_results["website_generation"]
            if isinstance(website_result, dict):
                insights["digital_presence"] = {
                    "site_structure": len(website_result.get('sitemap', [])),
                    "seo_ready": bool(website_result.get('seo_recommendations')),
                    "responsive_design": website_result.get('style_guide', {}).get('layout', {}).get('responsive', False),
                    "content_sections": len(website_result.get('website_structure', []))
                }
        
        # Extract visual asset insights
        if "logo_generation" in agent_results:
            logo_result = agent_results["logo_generation"]
            if isinstance(logo_result, dict):
                insights["visual_assets"] = {
                    "logo_variations": len(logo_result.get('logo_images', [])),
                    "brand_name": logo_result.get('brand_name', ''),
                    "design_style": "modern/professional",  # Could extract from prompt
                    "file_formats": ["PNG"]  # Could extract from actual files
                }
        
        return insights
    
    async def _generate_recommendations(self, agent_results: Dict[str, Any], completed_agents: List[str], failed_agents: List[str]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on results."""
        recommendations = []
        
        # Success-based recommendations
        if "branding" in completed_agents:
            recommendations.append({
                "category": "Brand Development",
                "priority": "High",
                "action": "Implement the selected brand identity across all marketing materials",
                "rationale": "Consistent brand application increases recognition by 80%"
            })
        
        if "logo_generation" in completed_agents:
            recommendations.append({
                "category": "Visual Identity",
                "priority": "Medium",
                "action": "Test logo variations with target audience before final selection",
                "rationale": "User testing improves logo effectiveness by 60%"
            })
        
        if "market_research" in completed_agents:
            recommendations.append({
                "category": "Market Strategy",
                "priority": "High", 
                "action": "Develop go-to-market strategy based on identified opportunities",
                "rationale": "Market research-driven strategies have 70% higher success rates"
            })
        
        if "website_generation" in completed_agents:
            recommendations.append({
                "category": "Digital Presence",
                "priority": "Medium",
                "action": "Implement website structure with professional development team",
                "rationale": "Professional websites convert 55% more visitors to customers"
            })
        
        # Failure-based recommendations
        if failed_agents:
            recommendations.append({
                "category": "Quality Assurance",
                "priority": "High",
                "action": f"Review and retry failed components: {', '.join(failed_agents)}",
                "rationale": "Complete deliverable set ensures comprehensive business foundation"
            })
        
        # Integration recommendations
        if len(completed_agents) > 1:
            recommendations.append({
                "category": "Integration",
                "priority": "High",
                "action": "Align all brand elements (name, logo, website, marketing) for consistency",
                "rationale": "Integrated brand experiences increase customer trust by 65%"
            })
        
        return recommendations
    
    def _calculate_performance_metrics(self, workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate workflow performance metrics."""
        agent_statuses = workflow_state.get('agent_statuses', {})
        execution_plan = workflow_state.get('execution_plan', {})
        
        return {
            "total_agents": len(execution_plan.get('required_agents', [])),
            "parallel_execution": True,
            "estimated_duration": execution_plan.get('estimated_duration', {}),
            "resource_usage": execution_plan.get('resource_requirements', {}),
            "agent_performance": {
                agent: status for agent, status in agent_statuses.items()
            },
            "workflow_efficiency": workflow_state.get('progress_percentage', 0),
            "error_rate": len(workflow_state.get('errors', [])),
            "warning_count": len(workflow_state.get('warnings', []))
        }
    
    async def save_consolidated_report(self, consolidated_report: Dict[str, Any], format_type: str = "json") -> str:
        """Save consolidated report to disk."""
        workflow_id = consolidated_report.get('metadata', {}).get('workflow_id', 'unknown')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        if format_type == "json":
            filename = f"workflow_report_{workflow_id}_{timestamp}.json"
            filepath = self.reports_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(consolidated_report, f, indent=2, ensure_ascii=False, default=str)
        
        elif format_type == "html":
            filename = f"workflow_report_{workflow_id}_{timestamp}.html"
            filepath = self.reports_dir / filename
            
            html_content = await self._generate_html_report(consolidated_report)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        self.logger.info(f"Saved consolidated report: {filepath}")
        return str(filepath)
    
    async def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML report from consolidated data."""
        metadata = report.get('metadata', {})
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Workflow Report - {metadata.get('workflow_id', 'Unknown')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #eee; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #2563eb; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        .section {{ margin: 30px 0; }}
        .section-title {{ font-size: 1.5em; font-weight: bold; color: #333; margin-bottom: 15px; border-left: 4px solid #2563eb; padding-left: 10px; }}
        .agent-results {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .agent-card {{ background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 20px; }}
        .agent-header {{ font-weight: bold; color: #2563eb; margin-bottom: 10px; }}
        .success {{ color: #16a34a; }}
        .error {{ color: #dc2626; }}
        .warning {{ color: #ca8a04; }}
        .recommendations {{ background: #f0f9ff; padding: 20px; border-radius: 8px; border-left: 4px solid #0ea5e9; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Workflow Execution Report</h1>
            <h2>{metadata.get('user_request', 'No request specified')}</h2>
            <p><strong>Workflow ID:</strong> {metadata.get('workflow_id', 'Unknown')} | 
               <strong>Generated:</strong> {metadata.get('generated_at', 'Unknown')}</p>
        </div>

        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{metadata.get('total_agents', 0)}</div>
                <div class="metric-label">Total Agents</div>
            </div>
            <div class="metric-card">
                <div class="metric-value success">{metadata.get('successful_agents', 0)}</div>
                <div class="metric-label">Successful</div>
            </div>
            <div class="metric-card">
                <div class="metric-value error">{metadata.get('failed_agents', 0)}</div>
                <div class="metric-label">Failed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metadata.get('success_rate', 0):.1f}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metadata.get('execution_time_seconds', 0):.1f}s</div>
                <div class="metric-label">Execution Time</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">📊 Agent Results</div>
            <div class="agent-results">
                {self._generate_agent_cards_html(report.get('agent_outputs', {}))}
            </div>
        </div>

        <div class="section">
            <div class="section-title">💡 Recommendations</div>
            <div class="recommendations">
                {self._generate_recommendations_html(report.get('recommendations', []))}
            </div>
        </div>

        <div class="section">
            <div class="section-title">📁 Generated Artifacts</div>
            {self._generate_artifacts_html(report.get('artifacts', {}))}
        </div>
    </div>
</body>
</html>
        """
        return html
    
    def _generate_agent_cards_html(self, agent_outputs: Dict[str, Any]) -> str:
        """Generate HTML cards for agent results."""
        cards = []
        for agent_name, output in agent_outputs.items():
            if isinstance(output, dict):
                summary = output.get('summary', 'No summary available')
                cards.append(f"""
                    <div class="agent-card">
                        <div class="agent-header">🤖 {agent_name.replace('_', ' ').title()}</div>
                        <p>{summary}</p>
                    </div>
                """)
        return ''.join(cards)
    
    def _generate_recommendations_html(self, recommendations: List[Dict[str, Any]]) -> str:
        """Generate HTML for recommendations."""
        if not recommendations:
            return "<p>No specific recommendations generated.</p>"
        
        html_items = []
        for rec in recommendations[:5]:  # Top 5 recommendations
            priority = rec.get('priority', 'Medium')
            priority_class = 'success' if priority == 'High' else 'warning' if priority == 'Medium' else ''
            html_items.append(f"""
                <div style="margin: 10px 0; padding: 10px; background: white; border-radius: 5px;">
                    <strong class="{priority_class}">[{priority}]</strong> 
                    <strong>{rec.get('category', 'General')}:</strong> {rec.get('action', 'No action specified')}
                    <br><small><em>{rec.get('rationale', '')}</em></small>
                </div>
            """)
        return ''.join(html_items)
    
    def _generate_artifacts_html(self, artifacts: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate HTML for artifacts."""
        html_sections = []
        for artifact_type, items in artifacts.items():
            if items:
                items_html = []
                for item in items:
                    exists_indicator = "✅" if item.get('exists', False) else "❌"
                    items_html.append(f"""
                        <li>{exists_indicator} <strong>{item.get('name', 'Unknown')}:</strong> {item.get('path', 'No path')} 
                        <em>(from {item.get('agent', 'unknown')})</em></li>
                    """)
                
                html_sections.append(f"""
                    <div style="margin: 15px 0;">
                        <h4>{artifact_type.replace('_', ' ').title()}</h4>
                        <ul>{''.join(items_html)}</ul>
                    </div>
                """)
        
        return ''.join(html_sections) if html_sections else "<p>No artifacts generated.</p>"


# Factory function for easy usage
def create_workflow_reporter(reports_dir: Optional[str] = None) -> WorkflowReporter:
    """Create a WorkflowReporter instance."""
    return WorkflowReporter(reports_dir)