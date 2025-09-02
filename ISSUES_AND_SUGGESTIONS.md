# Issues and Suggestions

## Issues

## Suggestions

### 1) Organizing Downloads [Implemented ([f73218c5](https://github.com/Jaynuke79/Social-Media-Downloader/commit/f73218c5204ad59965c0903623d09f7efcf4bf1c))] [Refined and Fixed ([5c0f9e4](https://github.com/Jaynuke79/Social-Media-Downloader/commit/5c0f9e4e926df06adc0a26cfff0efa1e455e1197))]


Have a subdirectory system within the default download location that organizes the downloads. 

An example being organizing by platform: If downloading from instagram, download the files in `<Default Download Location> -> Instagram -> <Author> -> <Download Files>` 

### 2) Downloading Additional Media Info [Implemented - Partial ([3b99fd0](https://github.com/Jaynuke79/Social-Media-Downloader/commit/3b99fd0db6d68a3cb0ad039076016028f2affe1f))]

Along with downloading the media, download comments, descriptions, and other additional info from the media in question. 

An example being downloading the comments of a tiktok video and saving them as a csv with the video of the video itself.

**Implementation Status:**
- ✅ **YouTube**: Full support - metadata, comments (CSV), descriptions, subtitles
- ⚠️ **TikTok**: Metadata and descriptions only - comments not available via yt-dlp extractor
- ⚠️ **Instagram**: Metadata and captions - comments require login authentication  
- ✅ **Other platforms**: Metadata support via yt-dlp

#### 2.1) Instagram Authentication for Enhanced Metadata

Implement Instagram login functionality to enable comment extraction and access to private content metadata.

**Current Limitation**: Instagram comment extraction fails with "Login required to access comments of a post" when `download_comments: true` is enabled.

**Suggested Implementation**:
- Add Instagram login configuration options (`instagram_username`, `instagram_password`)
- Implement secure credential storage (encrypted or prompted)
- Add session management for persistent login
- Enable comment extraction for public and followed accounts
- Add privacy controls for respecting account permissions

**Benefits**:
- Access to complete comment data for Instagram posts/reels
- Enhanced metadata for followed private accounts
- More comprehensive Instagram content archiving
- Better analytics and research capabilities

#### 2.2) Enhanced TikTok Comment Extraction

Implement alternative TikTok comment extraction methods since yt-dlp's TikTok extractor currently doesn't support comment downloads.

**Current Limitation**: TikTok videos download with full metadata and descriptions, but comments are not extracted despite `download_comments: true` configuration.

**Suggested Implementation Options**:
1. **Direct TikTok API Integration**: Research TikTok's official API for comment access
2. **Alternative Extractor**: Integrate specialized TikTok comment extraction tools
3. **Hybrid Approach**: Use yt-dlp for video/metadata, separate tool for comments
4. **Browser Automation**: Implement Selenium/Playwright for comment scraping (with rate limiting)

**Technical Considerations**:
- TikTok's anti-bot measures and rate limiting
- Comment pagination and threading
- Regional content restrictions
- API usage quotas and authentication requirements
