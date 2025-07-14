import QtQuick 2.15
import QtQuick.Controls 2.15
import Pisarz 1.0

Item {
    id: root
    
    property string content: embeddedBridge.content
    property bool hasChanges: embeddedBridge.hasChanges()
    
    signal editorContentChanged()
    signal editorSaveRequested(string content)
    
    EmbeddedEditorBridge {
        id: embeddedBridge
        
        onContentChanged: {
            root.editorContentChanged()
        }
        
        Component.onCompleted: {
            // Stwórz widget i embedduj go w tym komponencie
            var widget = embeddedBridge.create_widget()
            if (widget) {
                // Embedduj widget Qt w QML - UWAGA: to może nie działać tak jak oczekujemy
                // Qt Widgets nie mogą być bezpośrednio embeddowane w QML Item
                console.log("Widget stworzony, ale embedding może wymagać innego podejścia")
            }
        }
    }
    
    function setContent(content) {
        embeddedBridge.setContent(content)
    }
    
    function getContent() {
        return embeddedBridge.getContent()
    }
    
    function resetChanges() {
        embeddedBridge.resetChanges()
    }
}