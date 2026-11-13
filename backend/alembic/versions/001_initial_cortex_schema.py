"""initial cortex schema

Revision ID: 001
Revises: 
Create Date: 2026-11-13 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.db.vector_type import VectorType

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Attempt to enable pgvector extension if on PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=500), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('source_url', sa.String(length=2000), nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('word_count', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_docs_user_created', 'documents', ['user_id', 'created_at'])

    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('document_id', sa.String(length=36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('embedding', VectorType(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_chunks_user_doc', 'document_chunks', ['user_id', 'document_id'])

    op.create_table(
        'ingestion_jobs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('document_id', sa.String(length=36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column('progress_percent', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('error_log', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'conversations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False, server_default="default"),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'messages',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('conversation_id', sa.String(length=36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('reasoning_content', sa.Text(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'message_citations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('message_id', sa.String(length=36), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_id', sa.String(length=36), sa.ForeignKey('document_chunks.id', ondelete='SET NULL'), nullable=True),
        sa.Column('document_id', sa.String(length=36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('citation_index', sa.Integer(), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'research_reports',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('research_question', sa.Text(), nullable=False),
        sa.Column('executive_summary', sa.Text(), nullable=True),
        sa.Column('main_findings', sa.Text(), nullable=True),
        sa.Column('detailed_analysis', sa.Text(), nullable=True),
        sa.Column('contradictory_findings', sa.Text(), nullable=True),
        sa.Column('limitations', sa.Text(), nullable=True),
        sa.Column('unanswered_questions', sa.Text(), nullable=True),
        sa.Column('conclusion', sa.Text(), nullable=True),
        sa.Column('citations_json', sa.Text(), nullable=True),
        sa.Column('markdown_content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default="completed"),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'agent_tool_executions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('conversation_id', sa.String(length=36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('message_id', sa.String(length=36), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('tool_input_json', sa.Text(), nullable=True),
        sa.Column('tool_output_json', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('status', sa.String(length=50), nullable=False, server_default="success"),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'evaluation_datasets',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sample_count', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('samples_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'evaluation_runs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('dataset_id', sa.String(length=36), sa.ForeignKey('evaluation_datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default="completed"),
        sa.Column('recall_at_k', sa.Float(), nullable=False, server_default="0.0"),
        sa.Column('mrr', sa.Float(), nullable=False, server_default="0.0"),
        sa.Column('relevance_score', sa.Float(), nullable=False, server_default="0.0"),
        sa.Column('citation_precision', sa.Float(), nullable=False, server_default="0.0"),
        sa.Column('groundedness_score', sa.Float(), nullable=False, server_default="0.0"),
        sa.Column('avg_latency_ms', sa.Float(), nullable=False, server_default="0.0"),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('estimated_cost_usd', sa.Float(), nullable=False, server_default="0.0"),
        sa.Column('results_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'usage_records',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('request_type', sa.String(length=50), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('estimated_cost', sa.Float(), nullable=False, server_default="0.0"),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('usage_records')
    op.drop_table('evaluation_runs')
    op.drop_table('evaluation_datasets')
    op.drop_table('agent_tool_executions')
    op.drop_table('research_reports')
    op.drop_table('message_citations')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('ingestion_jobs')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
