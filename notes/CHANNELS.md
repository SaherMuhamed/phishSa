# Channel Selection in Wireless Networks

The channel number you choose for your fake AP (Access Point) significantly impacts several aspects of the wireless network:

## 1. Visibility and Connectivity
### Appearance in Network Lists:
- The channel number doesn't directly affect whether your AP appears in network lists.
- All channels in the 2.4GHz band (1-11/13 depending on country) are equally visible.
- However, choosing a less congested channel may make your AP more attractive to devices.

### Connection Reliability:
- Some channels are more prone to interference (see below).
- Channel selection affects how reliably devices can connect and maintain connection.

## 2. Speed and Performance
### Channel Width Considerations:
- Standard 20MHz channels (what hostapd uses by default) have consistent speed regardless of channel number.
- Adjacent channel interference can reduce effective speed.

### Interference Factors:
- **Channel Overlap**: In 2.4GHz, channels overlap with adjacent channels (1,6,11 are non-overlapping).
- **Congestion**: Some channels are more commonly used by:
  - Default router settings (often 6 or 11).
  - Bluetooth devices (interferes with channels 6-9).
  - Microwave ovens (affects channels 7-9).

## 3. Best Practices for Evil Twin Attacks
### For your educational purposes:
#### Recommended Channels:
- **Channel 1 or 11**: Often less congested than 6.
- **Channel 6**: Most common default, but more likely to have interference.
- **Avoid channels 7-9** due to microwave interference.

#### Technical Considerations:
- **Client Compatibility**:
  - All devices support all 2.4GHz channels (1-11/13).
  - Some enterprise networks may filter by channel.
- **Performance Impact**:
  - For a phishing AP, speed isn't critical (you're just serving a simple page).
  - Reliability is more important - choose a clean channel.
- **Detection Avoidance**:
  - Matching the real AP's channel makes your fake AP more believable.
  - Using an adjacent channel (especially +5/-5) can cause interference that makes the real AP unstable.
