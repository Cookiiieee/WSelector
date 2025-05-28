project('wselector', 'python3',
         version: '1.0.0',
         license: 'GPL-3.0')

python = import('python')

python3 = python.find_installation()

python3.add_project_arguments(
    '--install-scripts=${PREFIX}/bin',
    '--install-lib=${PYTHONDIR}',
    '--install-data=${DATADIR}',
)

python3.install()

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
