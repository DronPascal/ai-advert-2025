# ADR-0008: System Message Dividers

## Status
Accepted

## Context

Traditional chat applications struggle with distinguishing between actual conversation content and system events. Users need clear visual feedback when:

1. **Format Changes**: Understanding when AI response format has been updated
2. **Thread Management**: Knowing when new conversations begin or history is cleared  
3. **System Events**: Recognizing non-conversational state changes

Previous implementation mixed system notifications with user/assistant messages, creating confusion about conversation flow and making it unclear what was part of the actual dialogue versus system metadata.

## Decision

We will implement **elegant system message dividers** that visually separate system events from conversation content using a centered badge design with contextual icons.

### Visual Design

```
─────────────── 🔄 Формат ответов обновлен: JSON ───────────────
```

- **Horizontal divider lines** extending from chat edges
- **Centered badge** with background and rounded corners
- **Contextual icons** indicating event type
- **Minimal text** describing the system event
- **Material 3 styling** with muted colors

### System Event Types

| Event | Icon | Message |
|-------|------|---------|
| Format Change | 🔄 | "Формат ответов обновлен: {format_name}" |
| New Thread | ✨ | "Новая беседа начата" |
| History Clear | 🗑️ | "История беседы очищена" |
| Generic System | ℹ️ | Custom system message |

## Implementation Details

### UI Component Architecture

**SystemMessageDivider.kt**
```kotlin
@Composable
fun SystemMessageDivider(
    message: String,
    icon: String = "🔄",
    modifier: Modifier = Modifier
) {
    Row(/* centered layout with divider lines */) {
        HorizontalDivider(/* left line */)
        Box(/* central badge */) {
            Row {
                Text(icon)
                Text(message)
            }
        }
        HorizontalDivider(/* right line */)
    }
}
```

**MessageBubble Integration**
```kotlin
when (message.role) {
    MessageRole.SYSTEM -> {
        val (icon, text) = parseSystemMessage(message.content)
        SystemMessageDivider(
            message = text,
            icon = icon,
            modifier = modifier
        )
    }
    else -> {
        // Regular message bubble rendering
    }
}
```

### Message Role Enhancement

**Domain Model**
```kotlin
enum class MessageRole {
    USER,
    ASSISTANT,
    SYSTEM  // For system events and dividers
}
```

**Message Creation**
```kotlin
// In repository when format changes
val systemMessage = ChatMessage(
    id = UUID.randomUUID().toString(),
    content = "Формат ответов обновлен: ${format.name}",
    role = MessageRole.SYSTEM,
    timestamp = System.currentTimeMillis()
)
```

### Icon Selection Logic

**Smart Icon Detection**
```kotlin
private fun parseSystemMessage(content: String): Pair<String, String> {
    return when {
        content.contains("Формат ответов обновлен", ignoreCase = true) -> "🔄" to content
        content.contains("Новая беседа", ignoreCase = true) -> "✨" to content
        content.contains("История очищена", ignoreCase = true) -> "🗑️" to content
        else -> "ℹ️" to content
    }
}
```

## Technical Specifications

### Styling Requirements

**Material 3 Integration**
- `surfaceVariant` background with 70% opacity
- `outlineVariant` divider lines with 50% opacity  
- `onSurfaceVariant` text color
- 16dp corner radius for badge
- 12dp horizontal padding, 6dp vertical padding

**Responsive Design**
- Adapts to different screen widths
- Maintains centered alignment
- Scales with system font size preferences

### Performance Considerations

**Efficient Rendering**
- Minimal recomposition impact
- Lightweight composition structure
- No complex animations or effects
- Optimized for RecyclerView/LazyColumn usage

**Memory Usage**
- Single component instance per system message
- No retained state beyond props
- Minimal object allocation

### Database Integration

**System Message Storage**
```kotlin
// System messages stored alongside regular messages
ChatMessageEntity(
    id = "system_${UUID.randomUUID()}",
    content = "Новая беседа начата", 
    role = MessageRole.SYSTEM,
    timestamp = System.currentTimeMillis()
)
```

**Query Handling**
- System messages included in normal message flow
- Chronological ordering maintained
- No special filtering required

## Consequences

### Positive
✅ **Clear Visual Hierarchy**: System events visually distinct from conversation  
✅ **Contextual Understanding**: Icons provide immediate event type recognition  
✅ **Elegant Design**: Minimalist approach that doesn't overwhelm the UI  
✅ **Consistent Experience**: Unified treatment of all system events  
✅ **Accessibility**: Clear text and icons work with screen readers  
✅ **Maintainable**: Single component handles all system message types

### Negative
⚠️ **Additional Complexity**: New component and message parsing logic  
⚠️ **Icon Dependencies**: Relies on emoji for visual communication  
⚠️ **Localization**: Text content needs translation for international users

### Neutral
ℹ️ **Message Count**: System messages contribute to total message count  
ℹ️ **Storage Impact**: Minimal additional database storage required  
ℹ️ **Performance**: Negligible impact on rendering performance

## Usage Patterns

### Format Change Flow
1. User selects new format → Format dialog closes
2. System processes format change → Database updated
3. System message created → "🔄 Формат ответов обновлен: JSON"
4. Divider appears in chat → Clear visual feedback
5. AI responses follow new format → Immediate effect visible

### New Thread Creation
1. User clicks "New Thread" → Thread creation initiated
2. History cleared → Previous messages removed
3. System message created → "✨ Новая беседа начата"  
4. Clean slate established → Fresh conversation context
5. User can start new conversation → Clear beginning point

### History Management
1. User clears history → Confirmation and processing
2. All messages removed → Database cleaned
3. System message created → "🗑️ История беседы очищена"
4. User sees confirmation → Clear feedback about action
5. Fresh start available → No confusion about state

## Design Decisions

### Icon Selection Rationale

**🔄 (Format Changes)**
- Universal symbol for change/refresh
- Clearly indicates transformation
- Widely recognized across cultures

**✨ (New Thread)**  
- Positive, fresh start symbolism
- Indicates something new and special
- Friendly and approachable

**🗑️ (History Clear)**
- Direct representation of deletion
- Universally understood action
- Clear cause-and-effect association

**ℹ️ (Generic System)**
- Standard information symbol
- Neutral and professional
- Safe fallback for unknown events

### Color Scheme Rationale

**Muted Palette**
- Doesn't compete with conversation content
- Maintains focus on actual dialogue
- Professional and unobtrusive appearance

**Material 3 Compliance**
- Consistent with system design language
- Automatic dark/light theme support
- Accessibility standards compliance

## Future Enhancements

### Immediate Opportunities
- **Animated Entrance**: Subtle slide-in animation for new dividers
- **Tap Interactions**: Expandable details for complex system events
- **Custom Icons**: User-selectable icons for different event types

### Medium Term
- **Event Grouping**: Combine multiple rapid system events into single divider
- **Time Stamps**: Optional time display for system events
- **Action Buttons**: Quick actions directly from system dividers

### Long Term  
- **Smart Summarization**: AI-generated summaries of complex system events
- **Visual Themes**: User-customizable divider styles and colors
- **Advanced Context**: Rich previews of what changed in system events

## Testing Strategy

### Visual Testing
- Screenshot tests for different screen sizes
- Dark/light theme appearance validation
- Icon rendering across different devices
- Accessibility testing with screen readers

### Functional Testing
- System message creation triggers
- Icon selection logic accuracy
- Message parsing robustness
- Integration with existing message flow

### User Experience Testing
- Clarity of system event communication
- Visual hierarchy effectiveness
- User comprehension of different icons
- Overall conversation flow understanding

## References

- [Thread-Aware Format Updates](./ADR-0007-thread-aware-format-updates.md)
- [UI Responsiveness Improvements](./ADR-0006-ui-responsiveness-improvements.md)
- [Material 3 Design Guidelines](https://m3.material.io/)
- [Compose Best Practices](https://developer.android.com/jetpack/compose/mental-model)
