import json
import re
import uuid
from pathlib import Path
from datetime import datetime, timezone

class WorkspaceError(ValueError):
    pass

class WorkspaceStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.projects_dir = self.root / 'projects'
        self.artifacts_dir = self.root / 'artifacts'
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def _project_path(self, project_id):
        if not re.fullmatch(r'[a-f0-9]{12}', project_id):
            raise WorkspaceError('Invalid project ID')
        return self.projects_dir / (project_id + '.json')

    def create_project(self, name, description=''):
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            raise WorkspaceError('Enter a project name (max 120 characters)')
        now = datetime.now(timezone.utc).isoformat()
        item = {'id': uuid.uuid4().hex[:12], 'name': name.strip(), 'description': description.strip(), 'created_at': now, 'updated_at': now, 'notes': [], 'artifacts': []}
        self._write(item)
        return item

    def _write(self, item):
        path = self._project_path(item['id'])
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding='utf-8')
        temp.replace(path)

    def list_projects(self):
        items = []
        for path in self.projects_dir.glob('*.json'):
            try:
                items.append(json.loads(path.read_text(encoding='utf-8')))
            except (OSError, json.JSONDecodeError):
                pass
        return sorted(items, key=lambda item: item.get('updated_at', ''), reverse=True)

    def get_project(self, project_id):
        try:
            item = json.loads(self._project_path(project_id).read_text(encoding='utf-8'))
        except FileNotFoundError as exc:
            raise WorkspaceError('Project not found: ' + project_id) from exc
        if not isinstance(item, dict) or item.get('id') != project_id:
            raise WorkspaceError('Invalid project record')
        return item

    def add_note(self, project_id, note):
        if not isinstance(note, str) or not note.strip() or len(note) > 12000:
            raise WorkspaceError('Note must contain 1 to 12000 characters')
        item = self.get_project(project_id)
        item['notes'].append({'text': note.strip(), 'created_at': datetime.now(timezone.utc).isoformat()})
        item['updated_at'] = datetime.now(timezone.utc).isoformat()
        self._write(item)
        return item

    def save_artifact(self, filename, content, project_id=None):
        if not isinstance(filename, str) or not filename.strip() or not isinstance(content, str) or not content.strip():
            raise WorkspaceError('Filename and non-empty content are required')
        if len(content) > 200000:
            raise WorkspaceError('Artifact exceeds 200 KB')
        name = filename.strip()
        if not name.lower().endswith('.md'):
            name += '.md'
        if Path(name).name != name or not re.fullmatch(r'[\w .()-]+\.md', name, re.IGNORECASE):
            raise WorkspaceError('Use a filename only, without folders')
        path = self.artifacts_dir / name
        path.write_text(content.rstrip() + '\n', encoding='utf-8')
        if project_id:
            item = self.get_project(project_id)
            item['artifacts'].append({'filename': name, 'path': str(path), 'saved_at': datetime.now(timezone.utc).isoformat()})
            item['updated_at'] = datetime.now(timezone.utc).isoformat()
            self._write(item)
        return path
