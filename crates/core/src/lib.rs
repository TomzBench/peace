pub mod config;
use indoc::indoc;
use pyo3::prelude::*;

/// Run the Qdrant example from Python with logging configured
pub fn run_python_qdrant() -> PyResult<String> {
    Python::with_gil(|py| {
        // Configure Python logging to output to stdout with a format similar to Rust tracing
        py.run_bound(
            indoc! {r#"
                import logging
                import sys

                # Configure Python logging with a clean format
                logging.basicConfig(
                    level=logging.DEBUG,
                    format='%(levelname)-8s [python.%(name)s] %(message)s',
                    stream=sys.stdout,
                    force=True
                )
            "#},
            None,
            None,
        )?;

        // Run the Python code - logs will appear in stdout
        py.run_bound(
            indoc! {r#"
                from example import run_qdrant_example
                result = run_qdrant_example()
            "#},
            None,
            None,
        )?;

        Ok("Qdrant example completed successfully".to_string())
    })
}
