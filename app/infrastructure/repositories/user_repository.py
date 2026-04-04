from __future__ import annotations

from app.infrastructure.db import SessionLocal
from app.infrastructure.models import AppUser


class UserRepository:
    def get_by_username(self, username: str):
        db = SessionLocal()
        try:
            return db.query(AppUser).filter(AppUser.username == username).first()
        finally:
            db.close()

    def create_user(self, username: str, password_hash: str, role: str = "viewer"):
        db = SessionLocal()
        try:
            user = AppUser(
                username=username,
                password_hash=password_hash,
                role=role,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()

    def update_password(self, username: str, password_hash: str):
        db = SessionLocal()
        try:
            user = (
                db.query(AppUser)
                .filter(AppUser.username == username)
                .with_for_update()
                .first()
            )
            if user is None:
                return None
            user.password_hash = password_hash
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()

    def ensure_user(self, username: str, password_hash: str, role: str = "admin"):
        db = SessionLocal()
        try:
            user = db.query(AppUser).filter(AppUser.username == username).first()
            if user is None:
                user = AppUser(
                    username=username,
                    password_hash=password_hash,
                    role=role,
                    is_active=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                return user, True

            changed = False
            if user.password_hash != password_hash:
                user.password_hash = password_hash
                changed = True
            if user.role != role:
                user.role = role
                changed = True
            if not user.is_active:
                user.is_active = True
                changed = True
            if changed:
                db.commit()
                db.refresh(user)
            return user, False
        finally:
            db.close()

    def delete_by_username(self, username: str) -> int:
        db = SessionLocal()
        try:
            rows = db.query(AppUser).filter(AppUser.username == username).delete()
            db.commit()
            return rows
        finally:
            db.close()

    def delete_by_prefix_excluding(self, prefix: str, excluded_usernames: list[str] | None = None):
        db = SessionLocal()
        try:
            query = db.query(AppUser).filter(AppUser.username.like(f"{prefix}%"))
            if excluded_usernames:
                query = query.filter(~AppUser.username.in_(excluded_usernames))

            users = query.with_for_update().all()
            deleted_usernames = [user.username for user in users]
            for user in users:
                db.delete(user)
            db.commit()
            return deleted_usernames
        finally:
            db.close()

    def list_users(self):
        db = SessionLocal()
        try:
            return db.query(AppUser).order_by(AppUser.username.asc()).all()
        finally:
            db.close()

    def update_role(self, username: str, role: str):
        db = SessionLocal()
        try:
            user = (
                db.query(AppUser)
                .filter(AppUser.username == username)
                .with_for_update()
                .first()
            )
            if user is None:
                return None
            user.role = role
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()
