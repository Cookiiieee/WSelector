
# WSelector

<div align="center">
  <img src="https://i.ibb.co/YB6XHXmB/icon-1748228995-512x512.png" width="128" height="128" alt="WSelector Icon">
</div>

<div align="center">A modern GTK4/Adwaita application for browsing, downloading, and setting wallpapers from Wallhaven.cc website.</div>

##  Screenshot

<div align="center">
<img src="https://raw.githubusercontent.com/Cookiiieee/flathub/wselector-new-pr/screenshots/screenshot.png">
</div>

## ✨ Features

### Wallpaper Browsing
- Browse high-quality wallpapers from Wallhaven.cc
- Smooth infinite scrolling for seamless browsing
- Search functionality with debounce mechanism
- Filter by categories (General, Anime, People)
- Set purity levels (SFW, Sketchy)
- Sort by latest, popular, random
- Drag-to-pan functionality in preview mode
- Responsive image scaling and positioning

### Wallpaper Management
- Preview wallpapers
- One-click download and set as wallpaper
- View and manage downloaded wallpapers
- Automatic organization in `~/Pictures/WSelector/`

### User Experience
- Clean, modern GTK4/Adwaita interface
- Dark/Light theme support with system preference detection
- Toast notifications with action buttons
- Responsive design for all screen sizes
- Smooth animations and transitions
- Intuitive drag gestures for image navigation

## 🖥️ System Requirements

- Linux with Wayland or X11
- GTK 4.10 or later
- Python 3.12 (included in GNOME 48 runtime)
- Flatpak with Flathub repository configured
- Internet connection for wallpaper downloads

## 🚀 Installation

### Flatpak (Bundle) - Alternative

1. Add Clone repository:
   ```bash
   git clone https://github.com/Cookiiieee/WSelector.git
   cd WSelector
   flatpak-builder --user --install --force-clean build-dir io.github.Cookiiieee.WSelector.json
   ```
   
### Build from Source

1. Install prerequisites:
   ```bash
   # On Ubuntu/Debian
   sudo apt install flatpak flatpak-builder
   flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
   flatpak install flathub org.gnome.Sdk//48 org.gnome.Platform//48
   ```

2. Clone the repository and build:
   ```bash
   git clone https://github.com/Cookiiieee/WSelector.git
   cd WSelector
   flatpak-builder --user --install --force-clean build-dir io.github.Cookiiieee.WSelector.json
   ```

3. Run the application:
   ```bash
   flatpak run io.github.Cookiiieee.WSelector
   ```

### Permissions

The application requests the following permissions for full functionality:

- `--filesystem=home`: Required for:
  - Creating and executing temporary scripts to set wallpapers
  - Accessing configuration files
  - Creating necessary directories
  
- `--filesystem=xdg-pictures:create`: For saving wallpapers to `~/Pictures/WSelector/`

- Network access: Required to fetch wallpapers from Wallhaven.cc

- Wayland/X11 sockets: For proper display integration

## 📂 File Locations

- **Configuration**: `~/.var/app/io.github.Cookiiieee.WSelector/config/wselector/config.json`
- **Cache**: `~/.cache/wselector/` (thumbnails and temporary files)
- **Downloads**: `~/Pictures/WSelector/` (all downloaded wallpapers)
- **Logs**: `~/.var/app/io.github.Cookiiieee.WSelector/data/wselector/logs/` (debug information)

## 🔧 Troubleshooting

### Wallpaper Setting Issues
If wallpapers aren't setting correctly:
1. Ensure the application has the necessary permissions
2. Check that your desktop environment is supported (GNOME, KDE, XFCE, etc.)
3. Verify that the wallpaper directory exists and is writable
4. For Wayland users: Ensure `xdg-desktop-portal` is installed and running

### Performance Issues
If you experience any lag or stuttering:
1. Try reducing the number of concurrent downloads
2. Clear the thumbnail cache in `~/.cache/wselector/`
3. Restart the application to free up system resources

### Network Issues
If you encounter API errors:
1. Check your internet connection
2. Verify that Wallhaven.cc is accessible
3. The application implements retry logic for failed requests

## 🎯 Tips & Tricks

- Use the mouse wheel to quickly scroll through wallpapers in preview mode
- Right-click on any wallpaper to access quick actions
- Press `Esc` to close the preview window
- The application automatically saves your search preferences and last viewed position

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Wallhaven.cc](https://wallhaven.cc) for their amazing wallpaper collection.

## 🚧 Work in Progress
### App Memory Management (WIP)
The application is currently being enhanced with an advanced memory management system (`app_memory`) that will provide:
- Automatic memory usage optimization
- Intelligent caching of frequently used wallpapers
- Background memory cleanup of unused resources
- Memory usage analytics and reporting
- Configurable memory profiles for different system capabilities

This feature is currently under active development and will be included in an upcoming release.

[![Buy Me A Coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=☕&slug=cookiiieee&button_colour=5F7FFF&font_colour=ffffff&font_family=Poppins&outline_colour=000000&coffee_colour=FFDD00&font_size=14&height=28&width=150)](https://www.buymeacoffee.com/cookiiieee)
