mod commands;
mod plugins;

use plugins::permissions::PermissionManager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(PermissionManager::new())
        .invoke_handler(tauri::generate_handler![
            commands::file_ops::read_file,
            commands::file_ops::write_file,
            commands::file_ops::list_directory,
            commands::file_ops::delete_path,
            commands::file_ops::file_exists,
            commands::file_ops::create_directory,
            commands::file_ops::get_file_info,
            commands::shell::execute_command,
        ])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
