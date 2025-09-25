# =============================================================================
# 11. Bookmark API Routes (app/api/routes/bookmarks.py)
# =============================================================================

bookmark_router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])

class BookmarkRequest(BaseModel):
    user_id: str
    job_id: int

class BookmarkResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    created_at: datetime
    job: JobResponse
    
    class Config:
        from_attributes = True

@bookmark_router.post("/", response_model=dict)
@limiter.limit("20/minute")
async def create_bookmark(
    request: Request,
    bookmark_data: BookmarkRequest,
    db: Session = Depends(db_manager.get_db)
):
    """Create a job bookmark"""
    
    # Get or create user
    user = db.query(User).filter(User.user_id == bookmark_data.user_id).first()
    if not user:
        user = User(user_id=bookmark_data.user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Check if job exists
    job = db.query(Job).filter(Job.id == bookmark_data.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if bookmark already exists
    existing_bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == user.id,
        Bookmark.job_id == bookmark_data.job_id
    ).first()
    
    if existing_bookmark:
        raise HTTPException(status_code=400, detail="Job already bookmarked")
    
    # Create bookmark
    bookmark = Bookmark(user_id=user.id, job_id=bookmark_data.job_id)
    db.add(bookmark)
    db.commit()
    
    return {"message": "Bookmark created successfully"}

@bookmark_router.get("/", response_model=List[BookmarkResponse])
@limiter.limit("100/minute")
async def get_bookmarks(
    request: Request,
    user_id: str,
    db: Session = Depends(db_manager.get_db)
):
    """Get user's bookmarks"""
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return []
    
    bookmarks = db.query(Bookmark).filter(Bookmark.user_id == user.id).all()
    return bookmarks

@bookmark_router.delete("/{bookmark_id}")
@limiter.limit("20/minute")
async def delete_bookmark(
    request: Request,
    bookmark_id: int,
    user_id: str,
    db: Session = Depends(db_manager.get_db)
):
    """Delete a bookmark"""
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == user.id
    ).first()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    db.delete(bookmark)
    db.commit()
    
    return {"message": "Bookmark deleted successfully"}