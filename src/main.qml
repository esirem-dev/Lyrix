import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import Qt5Compat.GraphicalEffects
import QtCore

Window {
    visible: true
    width: 600*2
    height: 400*2
    title: "LyriX"
    visibility: isFullscreen ? "FullScreen" : "Windowed"
    id: main

    property QtObject backend
    property bool isFullscreen: false
    property bool isSynced: true
    property bool noLyrics: false
    property bool catMode: false
    property int selectedPositionIndex: 0
    property string subtextColor: "#dd000000"
    property string backgroundColor: "#fff"

    onIsFullscreenChanged: () => {
        if(isFullscreen){
            settings.lastXFullscreen = main.x
            settings.lastYFullscreen = main.y
        }

        settings.fullscreen = isFullscreen
    }

    function getIconePath(fileName){

        return "assets/img/icones/"+fileName
    }

    Image {
        id: imgCover
        height: 380
        width: 380

        source: ""
        smooth: true
        mipmap: true
    }

    Rectangle {
        id: backgroundRectangle
        anchors.fill: parent
        color: settings.nightMode ? "#000000" : backgroundColor

        Rectangle {
            color: "transparent"
            height: 450
            width: 450
            anchors.centerIn: parent
            opacity: 0.5
            visible: !(settings.nightMode == 2)

            GaussianBlur {
                anchors.centerIn: parent
                height: imgCover.height
                width: imgCover.width
                source: imgCover
                radius: 8
                samples: 16
                deviation: 4
                transparentBorder: true
            }
        }

        Rectangle {
            anchors.fill: parent
            color:"transparent"

            Image {
                id: backgroundImage
                anchors.fill: parent
                source: ""
                mipmap: true
                visible: !(settings.nightMode == 2)
            }
        }

        Rectangle {
            anchors.fill: parent
            color: "#00000000"
                
            ColumnLayout {
                anchors.fill: parent
                spacing: 5

                Rectangle {
                    Layout.preferredHeight: catMode ? parent.height*0.5 : parent.height
                    Layout.preferredWidth: parent.width
                    color: "transparent"

                    ListView {
                        anchors.centerIn: catMode ? undefined : parent
                        anchors.bottom: catMode ? parent.bottom : undefined
                        // anchors.top: catMode ? parent.top : undefined
                        height: isSynced ? listview.contentHeight : parent.height*0.8
                        width: parent.width
                        model: isSynced ? displayedLyrics : lyrics
                        interactive: !isSynced
                        id: listview

                        delegate: Text {
                            function pixelSize() {
                                if(selected)
                                    return 60*settings.sizeFontMultiplier
                                else
                                    if(isSynced)
                                        return 60*settings.sizeFontMultiplier*0.66
                                    else{
                                        let size = Math.round(60*settings.sizeFontMultiplier*0.70 - 1.5*Math.abs(index - selectedPositionIndex))
                                        if(size < 20)
                                            size = 20
                                        return size
                                    }
                            }
                            function _color(){
                                if(settings.nightMode == 2)
                                    return selected ? "#ddffffff" : "#ddaaaaaa"

                                if(isSynced)
                                    return selected ? "#ddffffff" : subtextColor
                                else{
                                    // let color = parseInt(subtextColor.substring(1, 7), 16)
                                    // let maxGap = 10
                                    // let gap = maxGap - Math.abs(index - selectedPositionIndex)
                                    // if(gap < 0)
                                    //     gap = 0
                                    // let red = (color >> 16) & 0xFF
                                    // let _red = red + ((255-red)/maxGap)*gap
                                    // let green = (color >> 8) & 0xFF
                                    // let _green = green + ((255-green)/maxGap)*gap
                                    // let blue = color & 0xFF
                                    // let _blue = blue + ((255-blue)/maxGap)*gap
                                    // let _color = "#" + ((_red << 16) | (_green << 8) | _blue).toString(16)
                                    return "#ddffffff"
                                }
                            }
                            text: textLyric 
                            font.pixelSize: pixelSize()
                            font.family: spotifyFont.name
                            font.letterSpacing: -1.5
                            color: _color()
                            width: listview.width
                            padding: isSynced ? 13 : 2
                            verticalAlignment: Text.AlignVCenter
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap

                            Behavior on font.pixelSize {
                                NumberAnimation {
                                    property: "font.pixelSize"
                                    duration: isSynced ? 0 : 250
                                    easing.type: Easing.OutCubic
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    color: "transparent"
                    Layout.preferredHeight: catMode ? parent.height*0.5 : 0
                    Layout.preferredWidth: parent.width

                    AnimatedImage { 
                        id: animation; 
                        anchors.top: parent.top
                        anchors.horizontalCenter: parent.horizontalCenter
                        source: "assets/img/cat-dancing2_boomerang.gif"

                        height: parent.height*0.7*settings.sizeFontMultiplier
                        fillMode: Image.PreserveAspectFit
                        speed: 1 // 120
                        // width: parent.width*0.5
                    }
                }
            }
        }
    }

    Rectangle {
        id: menuRectangle
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        z: 2
        height: 50
        opacity: 1
        width: listviewMenu.contentWidth
        color: "transparent"

        OpacityAnimator{
            id: menuOpacityAnimator
            from: 1;
            to: 0;
            duration: 400
            target: menuRectangle
        }

        Component {
            id: menuDelegate
            Rectangle{
                width: 50; height: 50
                color: "transparent"
                Image {
                    id: imgMenu
                    width: 35; height: 35
                    mipmap: true;
                    anchors.centerIn: parent
                    source: fileName()
                }

                MouseArea {
                    id: mouseAreaMenu
                    anchors.fill: imgMenu
                    hoverEnabled: true
                    propagateComposedEvents: true
                    cursorShape: menuRectangle.opacity ? Qt.PointingHandCursor : Qt.BlankCursor
                    onClicked: {
                        fnct();
                    }
                    onPositionChanged: () => {
                        menuRectangle.opacity = 1
                        timerMenu.restart()
                    }
                }

                Glow {
                    anchors.fill: imgMenu
                    radius: mouseAreaMenu.containsMouse ? (mouseAreaMenu.containsPress ? 8 : 5) : 3
                    samples: 12
                    color: settings.nightMode ? backgroundColor : "white"
                    source: imgMenu
                }
            }
        }
        
        ListModel {
            id: menuModel
            ListElement {
                fileName: () => { return getIconePath("settings.png") }
            }
            ListElement {
                fileName: () => { return settings.nightMode==2 ? getIconePath("daymode.png") : (settings.nightMode==1 ? getIconePath("nightmode2.png") : getIconePath("nightmode.png")) }
                fnct: () => {
                    settings.nightMode++;
                    if(settings.nightMode > 2)
                        settings.nightMode = 0;
                }
            }
            ListElement {
                fileName: () => { return isFullscreen ?  getIconePath("exit-fullscreen.png") : getIconePath("fullscreen.png") }
                fnct: () => {
                    isFullscreen = !isFullscreen;
                }
            }
        }

        ListView {
            id: listviewMenu
            anchors.fill: parent
            orientation: Qt.Horizontal
            layoutDirection: Qt.RightToLeft
            interactive: false
            model: menuModel
            delegate: menuDelegate
        }
    }

    Connections {
        target: backend
        
        function onClearLyrics() {
            lyrics.clear();
            updateDisplayedLyrics()
        }

        function onAddLyric(index, text){
            lyrics.set(index, {"textLyric": text, "selected": false, "hidden": index>1});
            updateDisplayedLyrics()
        }

        function onSelectLine(index){
            if(isSynced){
                for (let i = 0; i < lyrics.count ; i++) {
                    lyrics.setProperty(i, "selected", false)
                    if(i == index-1 || i == index+1)
                        lyrics.setProperty(i, "hidden", false)
                    else
                        lyrics.setProperty(i, "hidden", true)
                }
                lyrics.setProperty(index, "hidden", false)
                lyrics.setProperty(index, "selected", true)
            }else{
                listview.positionViewAtIndex(index, ListView.Center)
                selectedPositionIndex = index
            }
            updateDisplayedLyrics()
        }
        
        function onUpdateColor(background, text){
            backgroundColor = background;
            subtextColor = text;
            
            // let r = 255 - parseInt(background.substring(1,3), 16);
            // let g = 255 - parseInt(background.substring(3,5), 16);
            // let b = 255 - parseInt(background.substring(5,7), 16);
            // let negatifColor = "#aa" + r.toString(16) + g.toString(16) + b.toString(16);
            // console.log(background, negatifColor)
            // subtextColor = negatifColor;
        }

        function onUpdateCover(imgUrl){
            imgCover.source = imgUrl;
        }

        function onUpdateBackground(path){
            backgroundImage.source = path;
        }

        function onSetSyncType(type){
            if(type == "LINE_SYNCED"){
                isSynced = true;
            }else if(type == "UNSYNCED"){
                isSynced = false;
            }
        }

        function onSetNoLyrics(mode){
            noLyrics = mode;
        }
        
        function onUpdateBPM(bpm){
            let coef;
            if (bpm > 140){
                coef = 1.13
            }else{
                coef = 1.07
            }
            animation.speed = bpm/159*coef;
        }

        function updateDisplayedLyrics(){
            displayedLyrics.clear()
            for (let i = 0; i < lyrics.count ; i++) {
                if(!lyrics.get(i).hidden)
                    displayedLyrics.append(lyrics.get(i))
            }
        }
    }

    ListModel {
        id: lyrics
    }

    ListModel {
        id: displayedLyrics
    }

    FontLoader { id: spotifyFont; source: "assets/fonts/CircularStd-Black.otf" }

    Item {
        anchors.fill: parent
        focus: true
        Keys.onPressed: (event) => {
            if (event.key == Qt.Key_F11 || event.key == Qt.Key_F) {
                isFullscreen = !isFullscreen;
                event.accepted = true;
            }else if(event.key == Qt.Key_O){
                settings.sizeFontMultiplier = settings.sizeFontMultiplier - 0.1;
            }else if(event.key == Qt.Key_P){
                settings.sizeFontMultiplier = settings.sizeFontMultiplier + 0.1;
            }else if(event.key == Qt.Key_Escape){
                isFullscreen = false;
            }else if(event.key == Qt.Key_N){
                settings.nightMode++;
                if(settings.nightMode > 2)
                    settings.nightMode = 0;
            }else if(event.key == Qt.Key_C){
                catMode = !catMode;
            }
        }
    }

    Settings {
        id: settings
        property double sizeFontMultiplier: 1
        property int nightMode: 0
        property bool fullscreen: false
        property int monitorIndex: 0
        property int lastXFullscreen: 0
        property int lastYFullscreen: 0

        Component.onCompleted: {
            if(settings.fullscreen){
                main.x = settings.lastXFullscreen
                main.y = settings.lastYFullscreen
                isFullscreen = true;
            }

            // let screen = Qt.application.screens[settings.monitorIndex]
            // main.screen = screen
            // main.x = screen.virtualX + (screen.width - main.width)/2
            // main.y = screen.virtualY + (screen.height - main.height)/2
        }
    }
    
    Timer {
        id: timerMenu
        interval: 1500
        running: true
        onTriggered: () => {
            menuOpacityAnimator.start()
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        propagateComposedEvents: true
        cursorShape: menuRectangle.opacity ? Qt.ArrowCursor : Qt.BlankCursor
        onPositionChanged: () => {
            menuRectangle.opacity = 1
            timerMenu.restart()
        }
    }

    Component.onDestruction: {
        settings.sync();
    }
}