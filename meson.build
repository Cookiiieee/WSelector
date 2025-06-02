# Version for the next release
version = '0.1.4'

project('wselector', 'python3',
        version: version,
        license: 'GPL-3.0',
        meson_version: '>= 0.50.0')

# Python installation
python = import('python').find_installation('python3', required: true)

# Configure Python installation
python3 = python.find_installation('python3', required: true)
python3.install_sources(
    'wselector',
    pure: false,
    subdir: 'wselector'
)

# Install package data (if any)
install_subdir(
    'wselector/data',
    install_dir: python3.get_install_dir() / 'wselector',
    install_tag: 'python-module',
)

# Install desktop file
desktop_file = configure_file(
    input: 'wselector.desktop.in',
    output: 'io.github.Cookiiieee.WSelector.desktop',
    configuration: {
        'name': 'WSelector',
        'exec': 'wselector',
        'icon': 'io.github.Cookiiieee.WSelector',
        'type': 'Application',
        'categories': 'GTK;Utility;',
    }
)
install_data(desktop_file, install_dir: join_paths(get_option('datadir'), 'applications'))

# Install application icon
install_data(
    'icons/io.github.Cookiiieee.WSelector.svg',
    install_dir: join_paths(get_option('datadir'), 'icons/hicolor/scalable/apps')
)

# Install appdata file
install_data(
    'data/io.github.Cookiiieee.WSelector.appdata.xml',
    install_dir: join_paths(get_option('datadir'), 'metainfo')
)

# Install Python package
python.install_sources(
    'wselector',
    pure: false,
    subdir: 'wselector'
)

# Install package data (if any)
install_subdir(
    'wselector/data',
    install_dir: python.get_install_dir() / 'wselector',
    install_tag: 'python-module',
)

# Create entry point script
conf = configuration_data()
conf.set('PYTHON', python.full_path())
conf.set('PYTHONPATH', python.get_install_dir())
conf.set('pkgdatadir', get_option('prefix') / get_option('datadir') / 'wselector')

configure_file(
    input: 'wselector.in',
    output: 'wselector',
    configuration: conf,
    install: true,
    install_dir: get_option('bindir'),
    install_mode: 'rwxr-xr-x',
)

# Install icons
icon_sizes = ['16', '24', '32', '48', '64', '96', '128', '192', '256', '512', 'scalable']
foreach size : icon_sizes
    icon_dir = join_paths('icons', 'hicolor', size + 'x' + size, 'apps')
    install_data(
        join_paths(icon_dir, 'io.github.Cookiiieee.WSelector.svg'),
        install_dir: join_paths(get_option('datadir'), 'icons', 'hicolor', size + 'x' + size, 'apps')
    )
endforeach

# Install symbolic icon
install_data(
    'icons/hicolor/symbolic/apps/io.github.Cookiiieee.WSelector-symbolic.svg',
    install_dir: join_paths(get_option('datadir'), 'icons/hicolor/symbolic/apps')
)

# Install screenshot
install_data(
    'screenshots/screenshot.png',
    install_dir: join_paths(get_option('datadir'), 'app-info', 'icons')
)
