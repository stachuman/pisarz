import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Button {
    id: taskButton
    
    property string taskId: ""
    property string taskName: ""
    property string taskDescription: ""
    property bool isExecuting: false
    property color accentColor: "#4CAF50"
    
    signal taskRequested(string taskId)
    
    text: taskName
    enabled: !isExecuting
    
    implicitHeight: 40
    implicitWidth: 120
    
    background: Rectangle {
        color: taskButton.pressed ? Qt.darker(accentColor, 1.2) : 
               taskButton.hovered ? Qt.lighter(accentColor, 1.1) : 
               accentColor
        radius: 6
        border.color: taskButton.activeFocus ? Qt.lighter(accentColor, 1.3) : "transparent"
        border.width: 2
        
        // Subtle animation
        Behavior on color {
            ColorAnimation { duration: 150 }
        }
    }
    
    contentItem: RowLayout {
        spacing: 8
        
        // Loading indicator
        Rectangle {
            visible: isExecuting
            width: 16
            height: 16
            color: "transparent"
            
            Rectangle {
                width: 12
                height: 12
                radius: 6
                color: "white"
                anchors.centerIn: parent
                
                RotationAnimation on rotation {
                    running: isExecuting
                    loops: Animation.Infinite
                    from: 0
                    to: 360
                    duration: 1000
                }
            }
        }
        
        // Button text
        Text {
            text: taskButton.text
            color: "white"
            font.pointSize: 10
            font.weight: Font.Medium
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
    
    onClicked: {
        if (!isExecuting) {
            taskRequested(taskId)
        }
    }
    
    // Tooltip
    ToolTip.visible: hovered && taskDescription !== ""
    ToolTip.text: taskDescription
    ToolTip.delay: 1000
}