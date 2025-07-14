import QtQuick 2.15
import QtQuick.Controls 2.15
import Pisarz 1.0

Item {
    id: root
    
    property alias content: editor.content
    signal textChanged()
    
    RichTextEditor {
        id: editor
        
        Component.onCompleted: {
            var widget = editor.create_widget()
            if (widget) {
                widget.parent = root
                widget.anchors.fill = root
            }
        }
        
        onTextChanged: root.textChanged()
    }
    
    function setContent(content) {
        editor.setContent(content)
    }
    
    function getContent() {
        return editor.getContent()
    }
}