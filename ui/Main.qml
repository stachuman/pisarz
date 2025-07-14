import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import Pisarz 1.0

ApplicationWindow {
    id: window
    width: 1200
    height: 800
    visible: true
    title: qsTr("Pisarz - Writing Assistant")

    StackView {
        id: stackView
        anchors.fill: parent
        initialItem: ProjectListPage {}
    }
}
