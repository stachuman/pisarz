import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Pisarz 1.0

Page {
    id: sceneEditorPage
    title: qsTr("Edytor Sceny")

    required property int sceneId
    required property var sceneBridge
    
    property bool hasUnsavedChanges: nativeEditorBridge.hasChanges()
    property bool loadingContent: false

    header: Rectangle {
        height: 60
        color: "#2c3e50"
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            
            Button {
                text: qsTr("← Sceny")
                onClicked: stackView.pop()
            }
            
            Text {
                text: qsTr("Edytor Sceny - Zintegrowany RTF")
                color: "white"
                font.pixelSize: 16
                font.bold: true
                Layout.fillWidth: true
            }
            
            Text {
                text: hasUnsavedChanges ? qsTr("● Niezapisane") : qsTr("● Zapisane")
                color: hasUnsavedChanges ? "#e74c3c" : "#27ae60"
                font.pixelSize: 12
                font.bold: true
            }
            
            Button {
                text: qsTr("Zapisz")
                enabled: hasUnsavedChanges
                onClicked: saveScene()
                ToolTip.text: qsTr("Zapisz (Ctrl+S)")
            }
        }
    }

    // Area dla editora - z przyciskiem uruchamiającym
    Rectangle {
        anchors.fill: parent
        anchors.margins: 10
        color: "#f8f9fa"
        border.color: "#dee2e6"
        border.width: 1
        
        Column {
            anchors.centerIn: parent
            spacing: 20
            
            Rectangle {
                width: 64
                height: 64
                color: "#28a745"
                radius: 8
                anchors.horizontalCenter: parent.horizontalCenter
                
                Text {
                    anchors.centerIn: parent
                    text: "RTF"
                    color: "white"
                    font.pixelSize: 18
                    font.bold: true
                }
            }
            
            Text {
                text: qsTr("Edytor RTF")
                font.pixelSize: 20
                font.bold: true
                color: "#2c3e50"
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            Text {
                text: qsTr("Kliknij poniżej aby otworzyć edytor RTF\nz pełnym formatowaniem tekstu")
                font.pixelSize: 14
                color: "#6c757d"
                horizontalAlignment: Text.AlignHCenter
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            Button {
                text: qsTr("Otwórz Edytor RTF")
                anchors.horizontalCenter: parent.horizontalCenter
                onClicked: {
                    openRTFEditor()
                }
                
                background: Rectangle {
                    color: parent.pressed ? "#1e7e34" : (parent.hovered ? "#218838" : "#28a745")
                    radius: 6
                }
                
                contentItem: Text {
                    text: parent.text
                    color: "white"
                    font.pixelSize: 14
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }
    
    // Bridge do natywnego editora
    NativeEditorBridge {
        id: nativeEditorBridge
        
        onContentChanged: {
            hasUnsavedChanges = nativeEditorBridge.hasChanges()
        }
    }

    function openRTFEditor() {
        var sceneData = sceneBridge.getScene(sceneId)
        var sceneTitle = sceneData ? sceneData.title : "Scena"
        nativeEditorBridge.openEditor(sceneTitle)
    }

    function saveScene() {
        if (sceneId >= 0) {
            var content = nativeEditorBridge.getContent()
            var success = sceneBridge.updateSceneContent(sceneId, content)
            if (success) {
                nativeEditorBridge.resetChanges()
                hasUnsavedChanges = false
                console.log("Scena zapisana pomyślnie")
            } else {
                console.log("Błąd zapisywania sceny")
            }
        }
    }

    function loadScene() {
        if (sceneId >= 0) {
            loadingContent = true
            var sceneData = sceneBridge.getScene(sceneId)
            if (sceneData) {
                var content = sceneData.content_rtf || "<p>Zacznij pisać swoją scenę...</p>"
                nativeEditorBridge.setContent(content)
            }
            nativeEditorBridge.resetChanges()
            hasUnsavedChanges = false
            loadingContent = false
        }
    }

    // Handle keyboard shortcuts
    Shortcut {
        sequence: "Ctrl+S"
        onActivated: saveScene()
    }
    
    Component.onCompleted: {
        loadScene()
    }
}