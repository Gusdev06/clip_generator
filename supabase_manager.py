
import os
import json
from pathlib import Path
from supabase import create_client, Client
import config
from typing import Dict, Optional

class SupabaseManager:
    def __init__(self):
        self.url = config.SUPABASE_URL
        self.key = config.SUPABASE_KEY
        
        if not self.url or not self.key:
            print("⚠️ Supabase credentials not found. Skipping Supabase integration.")
            self.client = None
            return
            
        try:
            self.client: Client = create_client(self.url, self.key)
            self.bucket_name = config.SUPABASE_BUCKET_NAME
            self.table_name = config.SUPABASE_TABLE_NAME
        except Exception as e:
            print(f"❌ Error initializing Supabase client: {e}")
            self.client = None

    def upload_file(self, file_path: str, destination_path: str, content_type: str = None) -> Optional[str]:
        """
        Uploads a file to Supabase Storage and returns the public URL.
        """
        if not self.client:
            return None
            
        try:
            path = Path(file_path)
            if not path.exists():
                print(f"❌ File not found for upload: {file_path}")
                return None
                
            with open(file_path, 'rb') as f:
                file_options = {"upsert": "true"}
                if content_type:
                    file_options["content-type"] = content_type
                    
                self.client.storage.from_(self.bucket_name).upload(
                    path=destination_path,
                    file=f,
                    file_options=file_options
                )
                
            # Get public URL
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(destination_path)
            print(f"  ✓ Uploaded to Supabase: {destination_path}")
            return public_url
            
        except Exception as e:
            print(f"❌ Error uploading to Supabase: {e}")
            return None

    def save_clip_data(self, clip_metadata: Dict, video_url: str, json_url: str, youtube_url: str, job_id: str = None) -> Optional[Dict]:
        """
        Inserts a record into the generated_clips table.

        Args:
            clip_metadata: Metadata dict from the clip
            video_url: Public URL of the uploaded video
            json_url: Public URL of the uploaded JSON metadata
            youtube_url: Original YouTube video URL
            job_id: Job ID that generated this clip (optional)

        Returns:
            Dict with the created record data, or None if failed
        """
        if not self.client:
            return None

        try:
            data = {
                "youtube_url": youtube_url,
                "video_url": video_url,
                "json_url": json_url,
                "title": clip_metadata.get("suggested_titles_pt", ["Untitled"])[0],
                "viral_score": clip_metadata.get("viral_score", 0),
                "duration": clip_metadata.get("duration", 0),
                "category": clip_metadata.get("category", "General"),
                "job_id": job_id,  # Add job_id for tracking
                "metadata": clip_metadata # Store full metadata JSON
            }

            response = self.client.table(self.table_name).insert(data).execute()

            if response.data and len(response.data) > 0:
                record = response.data[0]
                print(f"  ✓ Saved clip record to database (ID: {record['id']})")
                return record
            else:
                print(f"  ⚠️  Warning: Insert succeeded but no data returned")
                return None

        except Exception as e:
            print(f"❌ Error saving to Supabase DB: {e}")
            return None
