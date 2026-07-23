"""
知识笔记 API — 觅投AI 金融知识教育平台

提供用户个人知识笔记的 CRUD + 搜索 + 统计功能。
支持分类、标签、置顶、全文搜索。

⚠️ 合规声明：笔记内容为用户个人记录，本平台不对其投资建议性负责
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.notes_service import notes_service, CATEGORIES

logger = logging.getLogger("mitouai.notes")

router = APIRouter()


# ═══════════════════════════════════════════════
#  请求模型
# ═══════════════════════════════════════════════

class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    content: str = Field("", max_length=50000, description="正文")
    category: str = Field("general", description="分类")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    is_pinned: bool = Field(False, description="是否置顶")
    is_public: bool = Field(False, description="是否公开")


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, max_length=50000)
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    is_pinned: Optional[bool] = None
    is_public: Optional[bool] = None


# ═══════════════════════════════════════════════
#  分类
# ═══════════════════════════════════════════════

@router.get("/categories")
async def get_categories():
    """获取笔记分类列表"""
    return {
        "categories": [{"key": k, "label": v} for k, v in CATEGORIES.items()],
    }


# ═══════════════════════════════════════════════
#  CRUD
# ═══════════════════════════════════════════════

@router.get("/")
async def list_notes(
    category: Optional[str] = Query(None, description="分类筛选: general/stocks/macro/strategy/factors/risk/lesson"),
    tag: Optional[str] = Query(None, description="标签筛选"),
    keyword: Optional[str] = Query(None, description="全文搜索关键词"),
    pinned: bool = Query(False, description="只看置顶"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """查询笔记列表（支持分类、标签、关键词筛选）"""
    try:
        result = notes_service.list_notes(
            category=category,
            tag=tag,
            keyword=keyword,
            pinned_only=pinned,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        logger.error(f"查询笔记列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """获取笔记统计信息"""
    try:
        return notes_service.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{note_id}")
async def get_note(note_id: int):
    """获取单条笔记详情"""
    note = notes_service.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return note


@router.post("/")
async def create_note(note: NoteCreate):
    """创建笔记"""
    try:
        if note.category not in CATEGORIES:
            note.category = "general"
        result = notes_service.create_note(
            title=note.title,
            content=note.content,
            category=note.category,
            tags=note.tags,
            is_pinned=note.is_pinned,
            is_public=note.is_public,
        )
        return {"success": True, "note": result}
    except Exception as e:
        logger.error(f"创建笔记失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{note_id}")
async def update_note(note_id: int, note: NoteUpdate):
    """更新笔记"""
    try:
        if note.category is not None and note.category not in CATEGORIES:
            note.category = "general"
        result = notes_service.update_note(
            note_id=note_id,
            title=note.title,
            content=note.content,
            category=note.category,
            tags=note.tags,
            is_pinned=note.is_pinned,
            is_public=note.is_public,
        )
        if not result:
            raise HTTPException(status_code=404, detail="笔记不存在")
        return {"success": True, "note": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新笔记失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{note_id}")
async def delete_note(note_id: int):
    """删除笔记"""
    try:
        success = notes_service.delete_note(note_id)
        if not success:
            raise HTTPException(status_code=404, detail="笔记不存在")
        return {"success": True, "message": "笔记已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除笔记失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
