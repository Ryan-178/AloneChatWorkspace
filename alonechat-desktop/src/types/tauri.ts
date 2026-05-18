export interface FileInfo {
  size: number;
  is_dir: boolean;
  is_file: boolean;
  modified: number;
}

export interface CommandResult {
  stdout: string;
  stderr: string;
  success: boolean;
  code: number | null;
}

export interface Workspace {
  path: string;
  name: string;
  files: string[];
  isExpanded?: boolean;
}

export interface PermissionState {
  allowedPaths: string[];
  allowedCommands: string[];
}
