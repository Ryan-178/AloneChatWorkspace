use std::collections::HashSet;
use std::sync::Mutex;

pub struct PermissionManager {
    allowed_paths: Mutex<HashSet<String>>,
    allowed_commands: Mutex<HashSet<String>>,
}

impl PermissionManager {
    pub fn new() -> Self {
        Self {
            allowed_paths: Mutex::new(HashSet::new()),
            allowed_commands: Mutex::new(HashSet::new()),
        }
    }

    pub fn grant_path(&self, path: String) {
        self.allowed_paths.lock().unwrap().insert(path);
    }

    pub fn revoke_path(&self, path: &str) {
        self.allowed_paths.lock().unwrap().remove(path);
    }

    pub fn is_path_allowed(&self, path: &str) -> bool {
        let allowed = self.allowed_paths.lock().unwrap();
        allowed.iter().any(|p| path.starts_with(p))
    }

    pub fn grant_command(&self, command: String) {
        self.allowed_commands.lock().unwrap().insert(command);
    }

    pub fn revoke_command(&self, command: &str) {
        self.allowed_commands.lock().unwrap().remove(command);
    }

    pub fn is_command_allowed(&self, command: &str) -> bool {
        self.allowed_commands.lock().unwrap().contains(command)
    }

    pub fn get_allowed_paths(&self) -> Vec<String> {
        self.allowed_paths.lock().unwrap().iter().cloned().collect()
    }

    pub fn get_allowed_commands(&self) -> Vec<String> {
        self.allowed_commands.lock().unwrap().iter().cloned().collect()
    }
}
