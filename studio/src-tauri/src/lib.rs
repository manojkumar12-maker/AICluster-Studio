mod launcher;

use launcher::discovery;
use launcher::health_manager;
use launcher::lifecycle::{self, LifecycleManager};
use launcher::process_manager;
use launcher::role_manager;
use std::sync::Arc;
use tauri::{
    Emitter,
    menu::{Menu, MenuItem, PredefinedMenuItem},
    tray::TrayIconBuilder,
    Manager,
};

fn handle_tray_menu(app: &tauri::AppHandle, id: &str) {
    match id {
        "show" | "dashboard" | "workers" | "logs" | "settings" => {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.set_focus();
                if id != "show" {
                    let _ = window.emit("navigate", id.to_string());
                }
            }
        }
        "restart" => {
            let app_handle = app.clone();
            tauri::async_runtime::spawn(async move {
                if let Some(lc) = launcher::lifecycle::get_lifecycle() {
                    let _ = lc.recovery_sequence("master").await;
                }
            });
        }
        "quit" => {
            let app_handle = app.clone();
            tauri::async_runtime::spawn(async move {
                if let Some(lc) = launcher::lifecycle::get_lifecycle() {
                    let _ = lc.shutdown_sequence().await;
                }
                app_handle.exit(0);
            });
        }
        _ => {}
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .setup(|app| {
            // Build system tray
            let show = MenuItem::with_id(app, "show", "Show AICluster Studio", true, None::<&str>)?;
            let dashboard = MenuItem::with_id(app, "dashboard", "Open Dashboard", true, None::<&str>)?;
            let workers = MenuItem::with_id(app, "workers", "Worker Manager", true, None::<&str>)?;
            let separator1 = PredefinedMenuItem::separator(app)?;
            let logs = MenuItem::with_id(app, "logs", "Open Logs", true, None::<&str>)?;
            let restart = MenuItem::with_id(app, "restart", "Restart Runtime", true, None::<&str>)?;
            let separator2 = PredefinedMenuItem::separator(app)?;
            let settings = MenuItem::with_id(app, "settings", "Settings", true, None::<&str>)?;
            let separator3 = PredefinedMenuItem::separator(app)?;
            let quit = MenuItem::with_id(app, "quit", "Quit AICluster", true, Some("Ctrl+Q"))?;

            let menu = Menu::with_items(app, &[
                &show, &dashboard, &workers, &separator1,
                &logs, &restart, &separator2,
                &settings, &separator3, &quit,
            ])?;

            TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .on_menu_event(|app, event| handle_tray_menu(app, event.id().as_ref()))
                .tooltip("AICluster Studio")
                .build(app)?;

            let lc = Arc::new(LifecycleManager::new().with_app_handle(app.handle().clone()));
            launcher::lifecycle::set_lifecycle(lc);

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            role_manager::get_role,
            role_manager::is_configured,
            role_manager::save_role,
            role_manager::get_runtime_dir,
            process_manager::start_service,
            process_manager::stop_service,
            process_manager::restart_service,
            process_manager::get_service_status,
            health_manager::check_health,
            health_manager::get_all_health_status,
            health_manager::is_master_healthy,
            health_manager::wait_for_master,
            discovery::scan_lan,
            discovery::detect_ai_providers,
            discovery::get_system_info,
            discovery::generate_secret,
            discovery::validate_connection,
            lifecycle::startup_services,
            lifecycle::shutdown_services,
            lifecycle::recover_service,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
