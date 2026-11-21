from __future__ import annotations

from datetime import date, time
from typing import List

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
    false,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    users: Mapped[List["User"]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    system_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )

    role: Mapped["Role"] = relationship(back_populates="users")

    work_days: Mapped[List["Day"]] = relationship(
        back_populates="marshall", foreign_keys="Day.marshall_id", passive_deletes=True
    )
    runs: Mapped[List["Run"]] = relationship(
        back_populates="customer",
        foreign_keys="Run.customer_id",
        cascade="all, delete-orphan",
    )


class Day(Base):
    __tablename__ = "days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    marshall_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    marshall: Mapped["User | None"] = relationship(
        back_populates="work_days", foreign_keys=[marshall_id]
    )
    available_hours: Mapped[List["AvailableHours"]] = relationship(
        back_populates="day", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("date", "marshall_id", name="uq_day_marshall_date"),
    )


class AvailableHours(Base):
    __tablename__ = "available_hours"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day_id: Mapped[int] = mapped_column(ForeignKey("days.id"), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    day: Mapped["Day"] = relationship(back_populates="available_hours")
    runs: Mapped[List["Run"]] = relationship(back_populates="available_hours")

    __table_args__ = (
        UniqueConstraint(
            "day_id", "start_time", "end_time", name="uq_available_hours_slot"
        ),
    )


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    available_hours_id: Mapped[int] = mapped_column(ForeignKey("available_hours.id"))
    total_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)

    customer: Mapped["User"] = relationship(
        back_populates="runs", foreign_keys=[customer_id]
    )
    available_hours: Mapped["AvailableHours"] = relationship(back_populates="runs")
    run_carts: Mapped[List["RunCart"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class CartModel(Base):
    __tablename__ = "cart_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(1000))
    model: Mapped[str] = mapped_column(String(255), nullable=False)

    carts: Mapped[List["Cart"]] = relationship(
        back_populates="cart_model", cascade="all, delete-orphan"
    )


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cart_model_id: Mapped[int] = mapped_column(
        ForeignKey("cart_models.id"), nullable=False
    )
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    cart_model: Mapped["CartModel"] = relationship(back_populates="carts")
    run_carts: Mapped[List["RunCart"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )


class RunCart(Base):
    __tablename__ = "run_carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"), nullable=False)

    run: Mapped["Run"] = relationship(back_populates="run_carts")
    cart: Mapped["Cart"] = relationship(back_populates="run_carts")

    __table_args__ = (UniqueConstraint("run_id", "cart_id", name="uq_run_cart"),)


class CartCenterData(Base):
    __tablename__ = "cart_center_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(String(1000), nullable=False)
    rules: Mapped[str] = mapped_column(String(1000), nullable=False)
