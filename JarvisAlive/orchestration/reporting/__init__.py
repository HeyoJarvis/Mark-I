"""
Workflow Reporting Package

Provides comprehensive result consolidation and reporting capabilities for parallel workflows.
"""

from .workflow_reporter import WorkflowReporter, create_workflow_reporter

__all__ = ['WorkflowReporter', 'create_workflow_reporter']