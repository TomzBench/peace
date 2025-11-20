use indoc::indoc;
use pyo3::prelude::*;

slint::include_modules!();

/// Run the Qdrant example from Python and capture output
fn run_python_qdrant() -> PyResult<String> {
    Python::with_gil(|py| {
        // Import sys to capture stdout
        let sys = py.import_bound("sys")?;

        // Create a StringIO object to capture output
        let io = py.import_bound("io")?;
        let string_io = io.getattr("StringIO")?.call0()?;

        // Redirect stdout to our StringIO
        sys.setattr("stdout", &string_io)?;

        // Run the Python code
        let result = py.run_bound(
            indoc! {r#"
                import sys
                from example import run_qdrant_example
                result = run_qdrant_example()
                print(f"\n{result}")
            "#},
            None,
            None,
        );

        // Get the captured output
        let output = string_io.call_method0("getvalue")?;
        let output_str: String = output.extract()?;

        // Restore stdout
        let original_stdout = py
            .import_bound("sys")?
            .getattr("__stdout__")?;
        sys.setattr("stdout", original_stdout)?;

        // Check if the run was successful
        result?;

        Ok(output_str)
    })
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize Python interpreter once
    pyo3::prepare_freethreaded_python();

    // Create the Slint UI
    let ui = AppWindow::new()?;

    // Setup the callback for running the search
    let ui_weak = ui.as_weak();
    ui.on_run_search(move || {
        let ui = ui_weak.unwrap();

        // Update status
        ui.set_status_text("Running Python backend...".into());
        ui.set_is_running(true);

        // Run the Python code
        match run_python_qdrant() {
            Ok(output) => {
                ui.set_output_log(output.into());
                ui.set_status_text("✓ Search completed successfully".into());
            }
            Err(e) => {
                let error_msg = format!("Error: {}\n{:?}", e, e);
                ui.set_output_log(error_msg.into());
                ui.set_status_text("✗ Error occurred".into());
            }
        }

        ui.set_is_running(false);
    });

    // Run the UI
    ui.run()?;

    Ok(())
}
