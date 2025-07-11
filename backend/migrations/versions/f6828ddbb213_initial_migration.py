"""Initial migration

Revision ID: f6828ddbb213
Revises: 
Create Date: 2025-06-08 12:33:36.926363

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6828ddbb213'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('password', sa.String(), nullable=True),
    sa.Column('user_type', sa.String(), nullable=True),
    sa.Column('jd_path', sa.String(), nullable=True),
    sa.Column('resume_path', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('interviews',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('interview_name', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interviews_id'), 'interviews', ['id'], unique=False)
    op.create_table('question_answers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('interview_id', sa.Integer(), nullable=True),
    sa.Column('question_id', sa.Integer(), nullable=True),
    sa.Column('question_text', sa.Text(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('answer_text', sa.Text(), nullable=True),
    sa.Column('camera_recording_path', sa.String(), nullable=True),
    sa.Column('screen_recording_path', sa.String(), nullable=True),
    sa.Column('audio_recording_path', sa.String(), nullable=True),
    sa.Column('combined_recording_path', sa.String(), nullable=True),
    sa.Column('ai_answer', sa.Text(), nullable=True),
    sa.Column('ai_remark', sa.Text(), nullable=True),
    sa.Column('candidate_score', sa.Float(), nullable=True),
    sa.Column('candidate_grade', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_question_answers_id'), 'question_answers', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_question_answers_id'), table_name='question_answers')
    op.drop_table('question_answers')
    op.drop_index(op.f('ix_interviews_id'), table_name='interviews')
    op.drop_table('interviews')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
