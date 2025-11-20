use anyhow::Result;
use indoc::indoc;
use peace_core::cli_config;
use std::io::Write;
use tracing::info;
use tracing_subscriber::{filter::LevelFilter, fmt, layer::SubscriberExt, prelude::*};

cli_config! {
    static config_path = "~/.config/peace/config.toml" as str, short='C', long="config";
    static verbose = false as bool, short='v', long="verbose";
    static version = false as bool, short='V', long="version";
    static help = false as bool, short='h', long="help";
}

fn print_help() {
    let _ = writeln!(
        std::io::stdout(),
        indoc! {r#"
        Usage: peace-cli [OPTION]

        Options:
        -C, --config     the configuration path
        -v, --verbose    use verbose logging
        -V, --version    print the version and exit
        -h, --help       print this help menu
        "#}
    );
}

fn print_version() {
    let _ = writeln!(std::io::stdout(), "{}", env!("CARGO_PKG_VERSION"));
}

fn main() -> Result<()> {
    let config = Config::parse_env()?;

    // Log help and exit if -h,--help
    if config.help {
        print_help();
        std::process::exit(0);
    }

    // Log version and exit if -V,--version
    if config.version {
        print_version();
        std::process::exit(0);
    }

    // Get debug flag
    let ll = if config.verbose {
        LevelFilter::DEBUG
    } else {
        LevelFilter::INFO
    };

    // Prepare stdout logging
    let stdout = fmt::layer()
        .compact()
        .with_ansi(true)
        .with_level(true)
        .with_file(false)
        .with_line_number(false)
        .with_target(true);

    // Initialize tracing subscriber
    tracing_subscriber::registry()
        .with(stdout)
        .with(ll)
        .init();

    info!("app ready");

    // Run Python code - Python logs will flow through pyo3-pylogger to tracing
    let result = peace_core::run_python_qdrant()?;
    info!("{}", result);

    Ok(())
}
