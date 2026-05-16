#pragma once

#include <string>

enum class FieldType {
    None,
    Psychic,
    Electric,
    Grassy,
    Misty,
    TrickRoom,
    Count
};

struct Field {
    FieldType type = FieldType::None;
    int duration = 0;
    int magicRoomTurns = 0;
    int wonderRoomTurns = 0;

    void setField(FieldType newType, int turns);
    void tick();
    bool isActive() const;
    bool isTrickRoom() const;
    bool isMagicRoom() const { return magicRoomTurns > 0; }
    bool isWonderRoom() const { return wonderRoomTurns > 0; }
    void setMagicRoomTurns(int turns) { magicRoomTurns = turns; }
    void setWonderRoomTurns(int turns) { wonderRoomTurns = turns; }
    std::string getName() const;
};
