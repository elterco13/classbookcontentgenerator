"""Guardado de trabajos en disco.

Cada trabajo vive en una carpeta con la fecha (DD-MM-YY), como los entregables:

    trabajos/17-11-26/
        job.json          estado completo (brief, fichas, versiones)
        01.png ... 06.png versión elegida de cada post
        versiones/        todas las versiones generadas (01_v1.png, 01_v2.png, ...)
        referencias/      imágenes de referencia subidas (07_ref.png, ...)
"""

import io
import os
import shutil
import zipfile
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .schemas import PostSpec

JOB_FILE = "job.json"
VERSIONS_DIR = "versiones"
REFERENCES_DIR = "referencias"


class ImageVersion(BaseModel):
    file: str  # ruta relativa a la carpeta del trabajo
    kind: Literal["generate", "edit"]
    model: str
    size: str
    prompt: str
    instruction: str = ""
    cost: float = 0.0
    created: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class PostState(BaseModel):
    spec: PostSpec
    style: str
    prompt_override: str = ""
    versions: list[ImageVersion] = Field(default_factory=list)
    selected: int = -1  # índice en versions; -1 = ninguna
    # Post basado en una imagen de referencia (ruta relativa); vacío = post normal.
    reference_file: str = ""

    @property
    def is_reference(self) -> bool:
        return bool(self.reference_file)

    @property
    def current(self) -> ImageVersion | None:
        if 0 <= self.selected < len(self.versions):
            return self.versions[self.selected]
        return None


class Job(BaseModel):
    id: str
    folder: str
    created: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    brief: str
    style: str
    posts: list[PostState]

    # ---------- rutas ----------
    def path(self, *parts: str) -> str:
        return os.path.join(self.folder, *parts)

    def final_name(self, idx: int) -> str:
        return f"{self.posts[idx].spec.number:02d}.png"

    # ---------- persistencia ----------
    def save(self) -> None:
        os.makedirs(self.folder, exist_ok=True)
        tmp = self.path(JOB_FILE + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))
        os.replace(tmp, self.path(JOB_FILE))

    @classmethod
    def load(cls, folder: str) -> "Job":
        with open(os.path.join(folder, JOB_FILE), encoding="utf-8") as f:
            job = cls.model_validate_json(f.read())
        job.folder = folder  # por si la carpeta se movió
        return job

    # ---------- imágenes ----------
    def add_version(self, idx: int, png: bytes, version: ImageVersion) -> None:
        post = self.posts[idx]
        n = len(post.versions) + 1
        rel = os.path.join(VERSIONS_DIR, f"{post.spec.number:02d}_v{n}.png")
        os.makedirs(self.path(VERSIONS_DIR), exist_ok=True)
        with open(self.path(rel), "wb") as f:
            f.write(png)
        version.file = rel
        post.versions.append(version)
        self.select(idx, len(post.versions) - 1)

    def select(self, idx: int, version_idx: int) -> None:
        post = self.posts[idx]
        post.selected = version_idx
        if post.current:
            shutil.copyfile(self.path(post.current.file), self.path(self.final_name(idx)))
        self.save()

    def add_reference_post(self, reference_png: bytes, instructions: str, texts: list[str], aspect_ratio: str) -> int:
        """Añade un post que adapta una imagen de referencia. Devuelve su índice."""
        number = max((p.spec.number for p in self.posts), default=0) + 1
        rel = os.path.join(REFERENCES_DIR, f"{number:02d}_ref.png")
        os.makedirs(self.path(REFERENCES_DIR), exist_ok=True)
        with open(self.path(rel), "wb") as f:
            f.write(reference_png)
        spec = PostSpec(
            number=number,
            brand_title="",
            scene=instructions.strip(),
            extra_text=[t.strip() for t in texts if t.strip()],
            aspect_ratio=aspect_ratio,
        )
        self.posts.append(PostState(spec=spec, style="reference", reference_file=rel))
        self.save()
        return len(self.posts) - 1

    def read_reference(self, idx: int) -> bytes | None:
        rel = self.posts[idx].reference_file
        if not rel or not os.path.exists(self.path(rel)):
            return None
        with open(self.path(rel), "rb") as f:
            return f.read()

    def read_current(self, idx: int) -> bytes | None:
        cur = self.posts[idx].current
        if not cur or not os.path.exists(self.path(cur.file)):
            return None
        with open(self.path(cur.file), "rb") as f:
            return f.read()

    def total_cost(self) -> float:
        return sum(v.cost for p in self.posts for v in p.versions)

    def zip_bytes(self) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for i, post in enumerate(self.posts):
                if post.current and os.path.exists(self.path(post.current.file)):
                    z.write(self.path(post.current.file), self.final_name(i))
        return buf.getvalue()


def new_job_folder(base_dir: str, when: datetime | None = None) -> tuple[str, str]:
    """Devuelve (id, carpeta) libres, p. ej. ('17-11-26', ...) o ('17-11-26_2', ...)."""
    when = when or datetime.now()
    base_id = f"{when.day:02d}-{when.month:02d}-{when.strftime('%y')}"
    job_id, n = base_id, 1
    while os.path.exists(os.path.join(base_dir, job_id)):
        n += 1
        job_id = f"{base_id}_{n}"
    return job_id, os.path.join(base_dir, job_id)


def list_jobs(base_dir: str) -> list[str]:
    """Carpetas de trabajos guardados, de la más reciente a la más antigua."""
    if not os.path.isdir(base_dir):
        return []
    folders = [
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if os.path.isfile(os.path.join(base_dir, d, JOB_FILE))
    ]
    return sorted(folders, key=lambda p: os.path.getmtime(os.path.join(p, JOB_FILE)), reverse=True)
