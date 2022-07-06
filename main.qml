import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import Qt.labs.settings 1.0

ApplicationWindow {
    visible: true
    width: 600*2
    height: 400*2
    title: "LyriX"
    visibility: isFullscreen ? "FullScreen" : "Windowed"
    id: main

    property QtObject backend
    property bool isFullscreen: false
    property bool isSynced: true
    property int selectedPositionIndex: 0
    property string subtextColor: "#dd000000"

    Image {
        id: imgCover
        height: 380
        width: 380

        source: "./background.png"
        smooth: true
        mipmap: true
    }

    Rectangle {
        id: backgroundRectangle
        anchors.fill: parent
        color: "#fff"

        Rectangle {
            color: "transparent"
            height: 450
            width: 450
            anchors.centerIn: parent
            opacity: 0.5

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
            color: "#00000000"
                
            ListView {
                anchors.centerIn: parent
                height: isSynced ? listview.contentHeight : parent.height*0.8
                width: parent.width
                model: lyrics
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
                    function color(){
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
                            return subtextColor
                        }
                    }
                    text: textLyric 
                    font.pixelSize: pixelSize()
                    font.family: spotifyFont.name
                    font.letterSpacing: -1.5
                    color: color()
                    width: listview.width
                    padding: isSynced ? 13 : 2
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    visible: !isSynced || !hidden
                    height: (hidden && isSynced) ? 0 : undefined
                }
            }
        }
    }

    Connections {
        target: backend
        
        function onClearLyrics() {
            lyrics.clear();
        }

        function onAddLyric(index, text){
            lyrics.set(index, {"textLyric": text, "selected": false, "hidden": false});
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
        }
        
        function onUpdateColor(background, text){
            backgroundRectangle.color = background;
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

        function onSetSyncType(type){
            if(type == "LINE_SYNCED"){
                isSynced = true;
            }else if(type == "UNSYNCED"){
                isSynced = false;
            }
        }
    }

    ListModel {
        id: lyrics
    }

    FontLoader { id: spotifyFont; source: "CircularStd-Black.otf" }

    Item {
        anchors.fill: parent
        focus: true
        Keys.onPressed: {
            if (event.key == Qt.Key_F11) {
                isFullscreen = !isFullscreen;
                event.accepted = true;
            }else if(event.key == Qt.Key_O){
                settings.sizeFontMultiplier = settings.sizeFontMultiplier - 0.1;
            }else if(event.key == Qt.Key_P){
                settings.sizeFontMultiplier = settings.sizeFontMultiplier + 0.1;
            }else if(event.key == Qt.Key_Escape){
                isFullscreen = false;
            }
        }
    }

    Settings {
        id: settings
        property double sizeFontMultiplier: 1;
    }
    
    Component.onDestruction: {
        settings.sync();
    }
}