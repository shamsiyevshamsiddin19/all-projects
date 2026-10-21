# -*- coding: utf-8 -*-
"""
Foldex Papkalar bilan ishlash xizmati (Folder Service).
Ushbu modul papkalar ierarxiyasini yaratish, tahrirlash, daraxt ko'rinishida
saralash, breadcrumb zanjirini tuzish va kaskadli tozalash amallarini bajaradi.
"""

from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.folder import Folder
from app.models.file_item import FileItem
from app.schemas.folder import BreadcrumbItem, FolderCreate, FolderOut, FolderTreeNode, FolderUpdate


class FolderService:
    """Papkalar bo'yicha barcha asinxron biznes mantiqni o'z ichiga olgan klass."""

    @staticmethod
    async def get_by_id(db: AsyncSession, folder_id: int) -> Optional[Folder]:
        """Berilgan ID ga ega papkani oladi."""
        result = await db.execute(select(Folder).where(Folder.id == folder_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_root_folders(db: AsyncSession) -> List[Folder]:
        """Asosiy (ildiz) papkalar ro'yxatini tartib indeksi va nomi bo'yicha oladi."""
        stmt = (
            select(Folder)
            .where(Folder.parent_id.is_(None))
            .order_by(Folder.order_index.asc(), Folder.name.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_subfolders(db: AsyncSession, parent_id: Optional[int]) -> List[Folder]:
        """Berilgan ota papkaning bevosita ichki papkalarini oladi."""
        if parent_id is None:
            return await FolderService.get_root_folders(db)

        stmt = (
            select(Folder)
            .where(Folder.parent_id == parent_id)
            .order_by(Folder.order_index.asc(), Folder.name.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_folder(db: AsyncSession, folder_in: FolderCreate) -> Folder:
        """Yangi papka yaratadi."""
        # Agar parent_id ko'rsatilgan bo'lsa, ota papka mavjudligini tekshiramiz
        if folder_in.parent_id is not None:
            parent = await FolderService.get_by_id(db, folder_in.parent_id)
            if not parent:
                raise ValueError("Ko'rsatilgan ota papka mavjud emas!")

        folder = Folder(
            name=folder_in.name.strip(),
            parent_id=folder_in.parent_id,
            icon=folder_in.icon or "📁",
            color=folder_in.color or "indigo",
            description=folder_in.description,
            order_index=folder_in.order_index or 0
        )
        db.add(folder)
        await db.commit()
        await db.refresh(folder)
        return folder

    @staticmethod
    async def update_folder(db: AsyncSession, folder_id: int, folder_in: FolderUpdate) -> Optional[Folder]:
        """Papkani yangilaydi (nomi, ikonkasi, ota papkasi va h.k.)."""
        folder = await FolderService.get_by_id(db, folder_id)
        if not folder:
            return None

        # Agar o'zini o'ziga yoki o'zining ichki bolalariga ota qilib qo'yishga urinsa - taqiqlash
        if folder_in.parent_id is not None:
            if folder_in.parent_id == folder_id:
                raise ValueError("Papka o'ziga ota bo'la olmaydi!")
            # Ota papka mavjudligini tekshirish
            parent = await FolderService.get_by_id(db, folder_in.parent_id)
            if not parent:
                raise ValueError("Ko'rsatilgan yangi ota papka topilmadi!")

        update_data = folder_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "name" and value is not None:
                setattr(folder, key, value.strip())
            else:
                setattr(folder, key, value)

        await db.commit()
        await db.refresh(folder)
        return folder

    @staticmethod
    async def delete_folder(db: AsyncSession, folder_id: int) -> Tuple[bool, List[str]]:
        """
        Papkani bazadan o'chiradi.
        Kaskadli o'chirish sababli uning barcha ichki bolalari va fayllari o'chadi.
        Diskdan fizik fayllarni ham tozalash uchun fayllarning nisbiy yo'llari ro'yxatini qaytaradi.
        """
        folder = await FolderService.get_by_id(db, folder_id)
        if not folder:
            return False, []

        # O'chirilishi kerak bo'lgan barcha ichki papkalar va ulardagi fayllarni yig'ish
        all_folder_ids = await FolderService._get_all_descendant_ids(db, folder_id)
        all_folder_ids.append(folder_id)

        # Shu papkalardagi fayllarning file_path larini olish
        file_paths_stmt = select(FileItem.file_path).where(FileItem.folder_id.in_(all_folder_ids))
        res = await db.execute(file_paths_stmt)
        file_paths = list(res.scalars().all())

        # Papkani bazadan o'chirish (DB kaskad orqali qolgan barcha bog'liqliklarni o'chiradi)
        await db.delete(folder)
        await db.commit()
        return True, file_paths

    @staticmethod
    async def _get_all_descendant_ids(db: AsyncSession, parent_id: int) -> List[int]:
        """Rekursiv ravishda barcha ichki papkalar identifikatorlarini yig'adi."""
        descendants = []
        stmt = select(Folder.id).where(Folder.parent_id == parent_id)
        res = await db.execute(stmt)
        children_ids = list(res.scalars().all())

        for child_id in children_ids:
            descendants.append(child_id)
            sub_ids = await FolderService._get_all_descendant_ids(db, child_id)
            descendants.extend(sub_ids)

        return descendants

    @staticmethod
    async def get_breadcrumbs(db: AsyncSession, folder_id: Optional[int]) -> List[BreadcrumbItem]:
        """
        Ildizdan boshlab joriy papkagacha bo'lgan navigatsiya zanjirini (Breadcrumbs) qaytaradi.
        Masalan: [Bosh sahifa -> Rus tili -> Grammatika -> Padejlar]
        """
        crumbs: List[BreadcrumbItem] = [
            BreadcrumbItem(id=None, name="Bosh sahifa", icon="🏠")
        ]
        if folder_id is None:
            return crumbs

        curr_id = folder_id
        path_nodes: List[BreadcrumbItem] = []

        while curr_id is not None:
            f = await FolderService.get_by_id(db, curr_id)
            if not f:
                break
            path_nodes.append(BreadcrumbItem(id=f.id, name=f.name, icon=f.icon))
            curr_id = f.parent_id

        # Orqadan oldinga tartiblash (chunki ildizdan boshlanishi kerak)
        path_nodes.reverse()
        crumbs.extend(path_nodes)
        return crumbs

    @staticmethod
    async def get_folder_with_stats(db: AsyncSession, folder: Folder) -> FolderOut:
        """Papkadagi ichki papkalar soni, fayllar soni va umumiy hajmni hisoblab FolderOut sxemasiga o'giradi."""
        # 1. Ichki papkalar soni
        sub_stmt = select(func.count(Folder.id)).where(Folder.parent_id == folder.id)
        sub_count = (await db.execute(sub_stmt)).scalar() or 0

        # 2. Fayllar soni va hajmi
        file_stmt = (
            select(
                func.count(FileItem.id),
                func.coalesce(func.sum(FileItem.file_size), 0)
            )
            .where(FileItem.folder_id == folder.id)
        )
        file_res = (await db.execute(file_stmt)).first()
        files_count = file_res[0] if file_res else 0
        total_size = file_res[1] if file_res else 0

        return FolderOut(
            id=folder.id,
            name=folder.name,
            parent_id=folder.parent_id,
            icon=folder.icon,
            color=folder.color,
            description=folder.description,
            order_index=folder.order_index,
            created_at=folder.created_at,
            updated_at=folder.updated_at,
            subfolders_count=sub_count,
            files_count=files_count,
            total_size_bytes=int(total_size)
        )

    @staticmethod
    async def get_folder_tree(db: AsyncSession) -> List[FolderTreeNode]:
        """Barcha papkalarni to'liq daraxt ko'rinishida yig'adi (Sidebar uchun)."""
        stmt = select(Folder).order_by(Folder.order_index.asc(), Folder.name.asc())
        res = await db.execute(stmt)
        all_folders = list(res.scalars().all())

        # Papkalarni xaritalash
        nodes_dict = {
            f.id: FolderTreeNode(
                id=f.id,
                name=f.name,
                icon=f.icon,
                color=f.color,
                parent_id=f.parent_id,
                children=[]
            )
            for f in all_folders
        }

        root_nodes: List[FolderTreeNode] = []
        for f in all_folders:
            node = nodes_dict[f.id]
            if f.parent_id and f.parent_id in nodes_dict:
                nodes_dict[f.parent_id].children.append(node)
            else:
                root_nodes.append(node)

        return root_nodes
