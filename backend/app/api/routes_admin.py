import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime

from app.api.deps import get_current_user, get_db
from app.db.models import User, Project
from app.core.security import get_password_hash
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


# ==================== Pydantic Models ====================

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime
    last_login_at: Optional[datetime] = None
    project_count: int

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "viewer"


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None


class StatsOut(BaseModel):
    total_users: int
    admin_count: int
    editor_count: int
    viewer_count: int
    total_projects: int
    total_versions: int


class TemplateOut(BaseModel):
    id: str
    name: str
    category: str
    description: str
    data_files: List[str] = []
    created_at: Optional[str] = None


class TemplateDetailOut(BaseModel):
    id: str
    name: str
    category: str
    description: str
    code: str
    data_files: List[str] = []


class TemplateCreate(BaseModel):
    category: str
    name: str
    description: str = ""
    code: str


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None


# ==================== Helper Functions ====================

def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def get_user_role(user: User) -> str:
    """Convert user model to role string"""
    if user.is_admin:
        return "admin"
    return "viewer"


def scan_templates_for_admin() -> List[TemplateOut]:
    """Scan templates directory and return template info list"""
    from app.api.routes_templates import get_template_description
    
    templates = []
    templates_path = settings.TEMPLATES_PATH
    
    if not os.path.exists(templates_path):
        return templates
    
    # 用于跟踪已处理的目录，避免重复
    processed_dirs = set()
    
    for category in os.listdir(templates_path):
        category_path = os.path.join(templates_path, category)
        if not os.path.isdir(category_path):
            continue
        
        for root, dirs, files in os.walk(category_path):
            py_files = [f for f in files if f.endswith('.py') and not f.startswith('__')]
            
            if not py_files:
                continue
            
            # 如果该目录已处理，跳过
            if root in processed_dirs:
                continue
            
            # 选择主要的 .py 文件
            dir_name = os.path.basename(root)
            main_py = None
            for pf in py_files:
                if pf.replace('.py', '') == dir_name:
                    main_py = pf
                    break
            if not main_py:
                main_py = max(py_files, key=lambda x: len(x))
            
            file_path = os.path.join(root, main_py)
            rel_path = os.path.relpath(file_path, templates_path)
            
            # 标记目录已处理
            processed_dirs.add(root)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
            except:
                code = ""
            
            # Find data files
            data_files = []
            parent_dir = os.path.dirname(file_path)
            for df in os.listdir(parent_dir):
                if df.endswith(('.csv', '.xlsx', '.xls')):
                    data_files.append(df)
            
            # Get template name
            template_name = os.path.basename(parent_dir)
            if template_name == category:
                template_name = main_py.replace('.py', '')
            
            # Get file modification time
            try:
                mtime = os.path.getmtime(file_path)
                created_at = datetime.fromtimestamp(mtime).isoformat()
            except:
                created_at = None
            
            templates.append(TemplateOut(
                id=rel_path,
                name=template_name,
                category=category,
                description=get_template_description(template_name, code),
                data_files=data_files,
                created_at=created_at
            ))
    
    return templates


# ==================== Stats Endpoints ====================

@router.get("/stats", response_model=StatsOut)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get system statistics"""
    total_users = db.query(func.count(User.id)).scalar()
    admin_count = db.query(func.count(User.id)).filter(User.is_admin == True).scalar()
    viewer_count = total_users - admin_count
    total_projects = db.query(func.count(Project.id)).scalar()
    
    return StatsOut(
        total_users=total_users,
        admin_count=admin_count,
        editor_count=0,  # No editor role in current model
        viewer_count=viewer_count,
        total_projects=total_projects,
        total_versions=0  # No versions in current model
    )


# ==================== User Management Endpoints ====================

@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all users"""
    users = db.query(User).all()
    result = []
    for user in users:
        project_count = db.query(func.count(Project.id)).filter(Project.owner_id == user.id).scalar()
        result.append(UserOut(
            id=user.id,
            username=user.username,
            role=get_user_role(user),
            created_at=user.created_at,
            last_login_at=None,
            project_count=project_count
        ))
    return result


@router.post("/users", response_model=UserOut)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new user"""
    # Check if username exists
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        is_admin=(user_data.role == "admin")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserOut(
        id=user.id,
        username=user.username,
        role=get_user_role(user),
        created_at=user.created_at,
        last_login_at=None,
        project_count=0
    )


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # Prevent removing last admin
    if user.is_admin and user_data.role and user_data.role != "admin":
        admin_count = db.query(func.count(User.id)).filter(User.is_admin == True).scalar()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能移除最后一个管理员"
            )
    
    if user_data.username:
        existing = db.query(User).filter(
            User.username == user_data.username,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        user.username = user_data.username
    
    if user_data.password:
        user.hashed_password = get_password_hash(user_data.password)
    
    if user_data.role:
        user.is_admin = (user_data.role == "admin")
    
    db.commit()
    db.refresh(user)
    
    project_count = db.query(func.count(Project.id)).filter(Project.owner_id == user.id).scalar()
    return UserOut(
        id=user.id,
        username=user.username,
        role=get_user_role(user),
        created_at=user.created_at,
        last_login_at=None,
        project_count=project_count
    )


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # Prevent deleting self
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    # Prevent deleting last admin
    if user.is_admin:
        admin_count = db.query(func.count(User.id)).filter(User.is_admin == True).scalar()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除最后一个管理员"
            )
    
    db.delete(user)
    db.commit()
    return {"message": "用户已删除"}


# ==================== Template Management Endpoints ====================

@router.get("/templates", response_model=List[TemplateOut])
def list_templates_admin(current_user: User = Depends(require_admin)):
    """List all templates (admin)"""
    return scan_templates_for_admin()


@router.get("/templates/categories", response_model=List[str])
def list_categories(current_user: User = Depends(require_admin)):
    """List all template categories"""
    templates_path = settings.TEMPLATES_PATH
    categories = []
    
    if os.path.exists(templates_path):
        for item in os.listdir(templates_path):
            if os.path.isdir(os.path.join(templates_path, item)):
                categories.append(item)
    
    return sorted(categories)


@router.get("/templates/{template_id:path}", response_model=TemplateDetailOut)
def get_template_admin(
    template_id: str,
    current_user: User = Depends(require_admin)
):
    """Get template details (admin)"""
    templates_path = settings.TEMPLATES_PATH
    file_path = os.path.join(templates_path, template_id)
    
    # Security check
    real_path = os.path.realpath(file_path)
    templates_real = os.path.realpath(templates_path)
    if not real_path.startswith(templates_real):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading template: {str(e)}")
    
    # Get category and name
    rel_path = os.path.relpath(file_path, templates_path)
    parts = rel_path.split(os.sep)
    category = parts[0] if parts else ""
    
    parent_dir = os.path.dirname(file_path)
    template_name = os.path.basename(parent_dir)
    if template_name == category:
        template_name = os.path.basename(file_path).replace('.py', '')
    
    # Find data files
    data_files = []
    for df in os.listdir(parent_dir):
        if df.endswith(('.csv', '.xlsx', '.xls')):
            data_files.append(df)
    
    from app.api.routes_templates import get_template_description
    
    return TemplateDetailOut(
        id=template_id,
        name=template_name,
        category=category,
        description=get_template_description(template_name, code),
        code=code,
        data_files=data_files
    )


@router.post("/templates", response_model=TemplateOut)
def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(require_admin)
):
    """Create a new template"""
    templates_path = settings.TEMPLATES_PATH
    
    # Create category directory if not exists
    category_path = os.path.join(templates_path, template_data.category)
    os.makedirs(category_path, exist_ok=True)
    
    # Create template directory
    template_dir = os.path.join(category_path, template_data.name)
    os.makedirs(template_dir, exist_ok=True)
    
    # Create Python file
    file_path = os.path.join(template_dir, f"{template_data.name}.py")
    
    # Add description as comment
    code_with_desc = f"# {template_data.description}\n{template_data.code}" if template_data.description else template_data.code
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(code_with_desc)
    
    rel_path = os.path.relpath(file_path, templates_path)
    
    return TemplateOut(
        id=rel_path,
        name=template_data.name,
        category=template_data.category,
        description=template_data.description,
        data_files=[],
        created_at=datetime.now().isoformat()
    )


@router.put("/templates/{template_id:path}", response_model=TemplateOut)
def update_template(
    template_id: str,
    template_data: TemplateUpdate,
    current_user: User = Depends(require_admin)
):
    """Update a template"""
    templates_path = settings.TEMPLATES_PATH
    file_path = os.path.join(templates_path, template_id)
    
    # Security check
    real_path = os.path.realpath(file_path)
    templates_real = os.path.realpath(templates_path)
    if not real_path.startswith(templates_real):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Update code if provided
    if template_data.code is not None:
        code_to_write = template_data.code
        if template_data.description:
            code_to_write = f"# {template_data.description}\n{template_data.code}"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code_to_write)
    
    # Get info for response
    rel_path = os.path.relpath(file_path, templates_path)
    parts = rel_path.split(os.sep)
    category = parts[0] if parts else ""
    
    parent_dir = os.path.dirname(file_path)
    template_name = template_data.name or os.path.basename(parent_dir)
    if template_name == category:
        template_name = os.path.basename(file_path).replace('.py', '')
    
    data_files = []
    for df in os.listdir(parent_dir):
        if df.endswith(('.csv', '.xlsx', '.xls')):
            data_files.append(df)
    
    return TemplateOut(
        id=template_id,
        name=template_name,
        category=category,
        description=template_data.description or "",
        data_files=data_files,
        created_at=None
    )


@router.delete("/templates/{template_id:path}")
def delete_template(
    template_id: str,
    current_user: User = Depends(require_admin)
):
    """Delete a template"""
    import shutil
    
    templates_path = settings.TEMPLATES_PATH
    file_path = os.path.join(templates_path, template_id)
    
    # Security check
    real_path = os.path.realpath(file_path)
    templates_real = os.path.realpath(templates_path)
    if not real_path.startswith(templates_real):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Delete the template directory (contains py file and any data files)
    template_dir = os.path.dirname(file_path)
    
    try:
        shutil.rmtree(template_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
    
    return {"message": "模板已删除"}
