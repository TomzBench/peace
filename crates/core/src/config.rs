#[macro_export]
macro_rules! cli_config {
    // Main entry with explicit flag patterns
    (
        $(
            static $name:ident = $value:literal as $kind:ident
            $(, short=$short:literal)?
            $(, long=$long:literal)?
        );* $(;)?
    ) => {
        // Generate Config struct
        #[derive(Debug, Clone)]
        pub struct Config {
            $(pub $name: cli_config!(@type $kind)),*
        }

        impl Default for Config {
            fn default() -> Self {
                Self {
                    $($name: cli_config!(@default_value $value, $kind)),*
                }
            }
        }

        // Generate parser
        impl Config {
            /// Parse configuration from environment args
            #[cfg_attr(test, allow(dead_code))]
            pub fn parse_env() -> Result<Self, lexopt::Error> {
                let parser = lexopt::Parser::from_env();
                Self::parse_impl(parser)
            }

            /// Parse configuration from provided args (useful for testing)
            pub fn parse_from<I>(args: I) -> Result<Self, lexopt::Error>
            where
                I: IntoIterator,
                I::Item: Into<std::ffi::OsString>,
            {
                let parser = lexopt::Parser::from_iter(args);
                Self::parse_impl(parser)
            }

            /// Internal implementation shared by parse_env and parse_from
            fn parse_impl(mut parser: lexopt::Parser) -> Result<Self, lexopt::Error> {
                use lexopt::prelude::*;
                let mut config = Self::default();

                while let Some(arg) = parser.next()? {
                    match arg {
                        $(
                            // Generate short match arm if short flag exists
                            $(Short($short) => {
                                cli_config!(@parse_value config, parser, $name, $kind)
                            },)?
                            // Generate long match arm if long flag exists
                            $(Long($long) => {
                                cli_config!(@parse_value config, parser, $name, $kind)
                            },)?
                        )*
                        _ => return Err(arg.unexpected()),
                    }
                }
                Ok(config)
            }
        }
    };

    // Type mappings
    (@type str) => { String };
    (@type int) => { i32 };
    (@type bool) => { bool };

    // Default value conversion
    (@default_value $value:literal, str) => { $value.to_string() };
    (@default_value $value:literal, int) => { $value };
    (@default_value $value:literal, bool) => { $value };

    // Value parsing - string
    (@parse_value $config:ident, $parser:ident, $name:ident, str) => {
        $config.$name = $parser.value()?.string()?
    };

    // Value parsing - int
    (@parse_value $config:ident, $parser:ident, $name:ident, int) => {
        $config.$name = $parser.value()?.parse()?
    };

    // Value parsing - bool (flag, no value needed)
    (@parse_value $config:ident, $parser:ident, $name:ident, bool) => {
        $config.$name = true
    };
}

#[cfg(test)]
mod tests {
    cli_config! {
        static config_path = "~/.config.json" as str, short='c', long="config";
        static max_retries = 3 as int, short='r', long="retries";
        static debug = false as bool, short='d', long="debug";
        static verbose = false as bool, long="verbose";
    }

    #[test]
    fn test_config_defaults() {
        let config = Config::default();
        assert_eq!(config.config_path, "~/.config.json");
        assert_eq!(config.max_retries, 3);
        assert!(!config.debug);
        assert!(!config.verbose);
    }

    #[test]
    fn test_parse_short_flags() {
        let config =
            Config::parse_from(["program", "-c", "/custom/path.json", "-r", "5", "-d"]).unwrap();

        assert_eq!(config.config_path, "/custom/path.json");
        assert_eq!(config.max_retries, 5);
        assert!(config.debug);
        assert!(!config.verbose); // not set, should be default
    }

    #[test]
    fn test_parse_long_flags() {
        let config = Config::parse_from([
            "program",
            "--config",
            "/etc/app.json",
            "--retries",
            "10",
            "--verbose",
        ])
        .unwrap();

        assert_eq!(config.config_path, "/etc/app.json");
        assert_eq!(config.max_retries, 10);
        assert!(!config.debug); // not set, should be default
        assert!(config.verbose);
    }

    #[test]
    fn test_parse_mixed_flags() {
        let config = Config::parse_from([
            "program",
            "-c",
            "/mixed.json",
            "--retries",
            "7",
            "-d",
            "--verbose",
        ])
        .unwrap();

        assert_eq!(config.config_path, "/mixed.json");
        assert_eq!(config.max_retries, 7);
        assert!(config.debug);
        assert!(config.verbose);
    }
}
