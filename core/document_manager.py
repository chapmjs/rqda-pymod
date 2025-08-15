# core/document_manager.py - Document Management Core Logic
import pandas as pd
import sqlalchemy as sa
from datetime import datetime
from typing import Optional, List, Dict, Any

class DocumentManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.db.create_tables()  # Ensure tables exist
    
    def create_file(self, name: str, content: str, owner: str = None, memo: str = None) -> int:
        """Create a new file record in the database"""
        size = len(content.encode('utf-8'))
        
        query = """
        INSERT INTO files (name, content, owner, memo, size) 
        VALUES (:name, :content, :owner, :memo, :size)
        """
        
        params = {
            'name': name,
            'content': content, 
            'owner': owner,
            'memo': memo,
            'size': size
        }
        
        with self.db.engine.connect() as conn:
            result = conn.execute(sa.text(query), params)
            conn.commit()
            return result.lastrowid
    
    def get_file(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get a single file by ID"""
        query = "SELECT * FROM files WHERE id = :file_id"
        
        with self.db.engine.connect() as conn:
            result = conn.execute(sa.text(query), {'file_id': file_id})
            row = result.fetchone()
            
        if row:
            return {
                'id': row[0],
                'name': row[1], 
                'content': row[2],
                'date_created': row[3],
                'date_modified': row[4],
                'owner': row[5],
                'memo': row[6],
                'size': row[7]
            }
        return None
    
    def get_all_files(self) -> pd.DataFrame:
        """Get all files as a pandas DataFrame"""
        query = """
        SELECT id, name, date_created, size, 
               CASE WHEN memo IS NOT NULL THEN 'Yes' ELSE 'No' END as has_memo
        FROM files 
        ORDER BY date_created DESC
        """
        
        with self.db.engine.connect() as conn:
            result = conn.execute(sa.text(query))
            rows = result.fetchall()
            
        if rows:
            df = pd.DataFrame(rows, columns=['id', 'name', 'date_created', 'size', 'has_memo'])
            # Format size in readable format
            df['size'] = df['size'].apply(self._format_file_size)
            return df
        else:
            return pd.DataFrame(columns=['id', 'name', 'date_created', 'size', 'has_memo'])
    
    def update_file(self, file_id: int, name: str = None, content: str = None, memo: str = None) -> bool:
        """Update file information"""
        updates = []
        params = {'file_id': file_id}
        
        if name is not None:
            updates.append("name = :name")
            params['name'] = name
            
        if content is not None:
            updates.append("content = :content")
            updates.append("size = :size") 
            params['content'] = content
            params['size'] = len(content.encode('utf-8'))
            
        if memo is not None:
            updates.append("memo = :memo")
            params['memo'] = memo
            
        if not updates:
            return False
            
        query = f"UPDATE files SET {', '.join(updates)} WHERE id = :file_id"
        
        with self.db.engine.connect() as conn:
            result = conn.execute(sa.text(query), params)
            conn.commit()
            return result.rowcount > 0
    
    def delete_file(self, file_id: int) -> bool:
        """Delete a file"""
        query = "DELETE FROM files WHERE id = :file_id"
        
        with self.db.engine.connect() as conn:
            result = conn.execute(sa.text(query), {'file_id': file_id})
            conn.commit()
            return result.rowcount > 0
    
    def search_files(self, search_term: str) -> pd.DataFrame:
        """Search files by name or content"""
        query = """
        SELECT id, name, date_created, size
        FROM files 
        WHERE name LIKE :search_term OR content LIKE :search_term
        ORDER BY date_created DESC
        """
        
        params = {'search_term': f'%{search_term}%'}
        
        with self.db.engine.connect() as conn:
            result = conn.execute(sa.text(query), params)
            rows = result.fetchall()
            
        if rows:
            df = pd.DataFrame(rows, columns=['id', 'name', 'date_created', 'size'])
            df['size'] = df['size'].apply(self._format_file_size)
            return df
        else:
            return pd.DataFrame(columns=['id', 'name', 'date_created', 'size'])
    
    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
            
        return f"{size_bytes:.1f}{size_names[i]}"

