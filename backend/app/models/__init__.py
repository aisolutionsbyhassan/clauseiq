# Models package — import all models for Alembic autogenerate and convenience
from app.models.user import User  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.contract import Contract  # noqa: F401
from app.models.document_chunk import DocumentChunk  # noqa: F401
from app.models.extracted_clause import ExtractedClause  # noqa: F401
from app.models.detected_risk import DetectedRisk  # noqa: F401
from app.models.executive_summary import ExecutiveSummary  # noqa: F401
from app.models.chat_message import ChatMessage  # noqa: F401
from app.models.comparison import Comparison  # noqa: F401
