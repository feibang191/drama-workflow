"""Phase 1-7: 交付组装 — 视频拼接 + SRT字幕 + 文件管理"""
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class VideoSegment:
    shot_id: str
    file_path: str
    duration: float
    subtitle_text: str = ""

@dataclass
class SubtitleEntry:
    index: int
    start: str  # "00:00:01,000"
    end: str
    text: str

class DeliveryAssembler:
    def __init__(self):
        self.segments: List[VideoSegment] = []
    
    def add_segment(self, segment: VideoSegment):
        self.segments.append(segment)
    
    def generate_subtitles(self, start_offset: float = 0) -> str:
        """生成SRT字幕内容"""
        entries = []
        current_time = start_offset
        for i, seg in enumerate(self.segments, 1):
            if seg.subtitle_text:
                start = self._fmt_time(current_time)
                end = self._fmt_time(current_time + seg.duration)
                entries.append(SubtitleEntry(i, start, end, seg.subtitle_text))
            current_time += seg.duration
        
        # 构建SRT
        lines = []
        for e in entries:
            lines.append(str(e.index))
            lines.append(f"{e.start} --> {e.end}")
            lines.append(e.text)
            lines.append("")
        return "\n".join(lines)
    
    def get_ffmpeg_concat_cmd(self, output_path: str) -> str:
        """生成ffmpeg拼接命令"""
        filelist = "\n".join(f"file '{s.file_path}'" for s in self.segments)
        return f'echo -e "{filelist}" > concat.txt && ffmpeg -f concat -safe 0 -i concat.txt -c copy "{output_path}"'
    
    def get_asset_stats(self) -> dict:
        return {
            "segments": len(self.segments),
            "total_duration": sum(s.duration for s in self.segments),
            "files": [s.file_path for s in self.segments],
        }
    
    @staticmethod
    def _fmt_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
