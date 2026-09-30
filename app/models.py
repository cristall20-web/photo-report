from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    report_date = Column(String(20), nullable=False)
    address = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("ReportItem", back_populates="report",
                         cascade="all, delete-orphan")


class ReportItem(Base):
    __tablename__ = "report_items"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"))
    object_name = Column(String(100))
    executor = Column(String(100))
    description = Column(Text)
    photo_path = Column(String(500))
    order_num = Column(Integer, default=0)

    report = relationship("Report", back_populates="items")