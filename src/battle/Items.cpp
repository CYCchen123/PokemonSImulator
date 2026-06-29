#include "battle/Items.h"
#include "battle/Pokemon.h"
#include "battle/Battle.h"
#include "battle/PRNG.h"
#include "battle/Types.h"
#include "battle/Status.h"
#include "battle/GameRegistry.h"
#include <algorithm>
#include <limits>
#include <cctype>

namespace {
const ItemDamageContext* toDamageContext(void* context) {
    return static_cast<const ItemDamageContext*>(context);
}

bool tookDamageFromDamagingMove(const ItemDamageContext* ctx) {
    return ctx && ctx->isDamagingMove && ctx->damage > 0;
}
}

Item getItem(ItemType type) {
    return GameRegistry::instance().getItem(type);
}

std::string getItemName(ItemType type) {
    switch (type) {
        case ItemType::OranBerry: return "Oran Berry";
        case ItemType::SitrusBerry: return "Sitrus Berry";
        case ItemType::LumBerry: return "Lum Berry";
        case ItemType::ChestoBerry: return "Chesto Berry";
        case ItemType::PechaBerry: return "Pecha Berry";
        case ItemType::RawstBerry: return "Rawst Berry";
        case ItemType::AspearBerry: return "Aspear Berry";
        case ItemType::PersimBerry: return "Persim Berry";
        case ItemType::CheriBerry: return "Cheri Berry";
        case ItemType::FigyBerry: return "Figy Berry";
        case ItemType::WikiBerry: return "Wiki Berry";
        case ItemType::MagoBerry: return "Mago Berry";
        case ItemType::AguavBerry: return "Aguav Berry";
        case ItemType::IapapaBerry: return "Iapapa Berry";
        case ItemType::OccaBerry: return "Occa Berry";
        case ItemType::PasshoBerry: return "Passho Berry";
        case ItemType::WacanBerry: return "Wacan Berry";
        case ItemType::RindoBerry: return "Rindo Berry";
        case ItemType::YacheBerry: return "Yache Berry";
        case ItemType::ChopleBerry: return "Chople Berry";
        case ItemType::KebiaBerry: return "Kebia Berry";
        case ItemType::ShucaBerry: return "Shuca Berry";
        case ItemType::CobaBerry: return "Coba Berry";
        case ItemType::PayapaBerry: return "Payapa Berry";
        case ItemType::TangaBerry: return "Tanga Berry";
        case ItemType::ChartiBerry: return "Charti Berry";
        case ItemType::KasibBerry: return "Kasib Berry";
        case ItemType::HabanBerry: return "Haban Berry";
        case ItemType::ColburBerry: return "Colbur Berry";
        case ItemType::BabiriBerry: return "Babiri Berry";
        case ItemType::ChilanBerry: return "Chilan Berry";
        case ItemType::LiechiBerry: return "Liechi Berry";
        case ItemType::GanlonBerry: return "Ganlon Berry";
        case ItemType::SalacBerry: return "Salac Berry";
        case ItemType::PetayaBerry: return "Petaya Berry";
        case ItemType::ApicotBerry: return "Apicot Berry";
        case ItemType::JabocaBerry: return "Jaboca Berry";
        case ItemType::RowapBerry: return "Rowap Berry";
        case ItemType::Leftovers: return "Leftovers";
        case ItemType::BlackSludge: return "Black Sludge";
        case ItemType::ShellBell: return "Shell Bell";
        case ItemType::ChoiceBand: return "Choice Band";
        case ItemType::ChoiceSpecs: return "Choice Specs";
        case ItemType::ChoiceScarf: return "Choice Scarf";
        case ItemType::QuickClaw: return "Quick Claw";
        case ItemType::LifeOrb: return "Life Orb";
        case ItemType::ExpertBelt: return "Expert Belt";
        case ItemType::MuscleBand: return "Muscle Band";
        case ItemType::WiseGlasses: return "Wise Glasses";
        case ItemType::LightBall: return "Light Ball";
        case ItemType::QuickPowder: return "Quick Powder";
        case ItemType::ThickClub: return "Thick Club";
        case ItemType::MetalPowder: return "Metal Powder";
        case ItemType::DeepSeaTooth: return "Deep Sea Tooth";
        case ItemType::DeepSeaScale: return "Deep Sea Scale";
        case ItemType::PowerHerb: return "Power Herb";
        case ItemType::StickyBarb: return "Sticky Barb";
        case ItemType::BigRoot: return "Big Root";
        case ItemType::KingsRock: return "King's Rock";
        case ItemType::WideLens: return "Wide Lens";
        case ItemType::ZoomLens: return "Zoom Lens";
        case ItemType::ScopeLens: return "Scope Lens";
        case ItemType::SilverPowder: return "Silver Powder";
        case ItemType::MetalCoat: return "Metal Coat";
        case ItemType::HardStone: return "Hard Stone";
        case ItemType::MiracleSeed: return "Miracle Seed";
        case ItemType::BlackGlasses: return "Black Glasses";
        case ItemType::BlackBelt: return "Black Belt";
        case ItemType::Magnet: return "Magnet";
        case ItemType::MysticWater: return "Mystic Water";
        case ItemType::SharpBeak: return "Sharp Beak";
        case ItemType::PoisonBarb: return "Poison Barb";
        case ItemType::NeverMeltIce: return "Never-Melt Ice";
        case ItemType::SpellTag: return "Spell Tag";
        case ItemType::TwistedSpoon: return "Twisted Spoon";
        case ItemType::Charcoal: return "Charcoal";
        case ItemType::DragonFang: return "Dragon Fang";
        case ItemType::SilkScarf: return "Silk Scarf";
        case ItemType::SeaIncense: return "Sea Incense";
        case ItemType::FlamePlate: return "Flame Plate";
        case ItemType::SplashPlate: return "Splash Plate";
        case ItemType::ZapPlate: return "Zap Plate";
        case ItemType::MeadowPlate: return "Meadow Plate";
        case ItemType::IciclePlate: return "Icicle Plate";
        case ItemType::FistPlate: return "Fist Plate";
        case ItemType::ToxicPlate: return "Toxic Plate";
        case ItemType::EarthPlate: return "Earth Plate";
        case ItemType::SkyPlate: return "Sky Plate";
        case ItemType::MindPlate: return "Mind Plate";
        case ItemType::InsectPlate: return "Insect Plate";
        case ItemType::StonePlate: return "Stone Plate";
        case ItemType::SpookyPlate: return "Spooky Plate";
        case ItemType::IronPlate: return "Iron Plate";
        case ItemType::FlameOrb: return "Flame Orb";
        case ItemType::ToxicOrb: return "Toxic Orb";
        case ItemType::FocusSash: return "Focus Sash";
        case ItemType::RockyHelmet: return "Rocky Helmet";
        case ItemType::AirBalloon: return "Air Balloon";
        case ItemType::Eviolite: return "Eviolite";
        case ItemType::AssaultVest: return "Assault Vest";
        case ItemType::RedCard: return "Red Card";
        case ItemType::EjectButton: return "Eject Button";
        case ItemType::WhiteHerb: return "White Herb";
        case ItemType::WeaknessPolicy: return "Weakness Policy";
        case ItemType::BerryJuice: return "Berry Juice";
        case ItemType::HeavyDutyBoots: return "Heavy-Duty Boots";
        case ItemType::CovertCloak: return "Covert Cloak";
        case ItemType::ClearAmulet: return "Clear Amulet";
        case ItemType::ProtectivePads: return "Protective Pads";
        case ItemType::PunchingGlove: return "Punching Glove";
        case ItemType::BoosterEnergy: return "Booster Energy";
        case ItemType::LoadedDice: return "Loaded Dice";
        case ItemType::MirrorHerb: return "Mirror Herb";
        case ItemType::AbilityShield: return "Ability Shield";
        case ItemType::EjectPack: return "Eject Pack";
        case ItemType::TerrainExtender: return "Terrain Extender";
        case ItemType::RoomService: return "Room Service";
        case ItemType::BlunderPolicy: return "Blunder Policy";
        case ItemType::ThroatSpray: return "Throat Spray";
        case ItemType::UtilityUmbrella: return "Utility Umbrella";
        case ItemType::LightClay: return "Light Clay";
        case ItemType::MentalHerb: return "Mental Herb";
        case ItemType::SafetyGoggles: return "Safety Goggles";
        case ItemType::RingTarget: return "Ring Target";
        case ItemType::Metronome: return "Metronome";
        case ItemType::DampRock: return "Damp Rock";
        case ItemType::HeatRock: return "Heat Rock";
        case ItemType::IcyRock: return "Icy Rock";
        case ItemType::SmoothRock: return "Smooth Rock";
        case ItemType::BrightPowder: return "Bright Powder";
        case ItemType::FocusBand: return "Focus Band";
        case ItemType::CustapBerry: return "Custap Berry";
        case ItemType::EnigmaBerry: return "Enigma Berry";
        case ItemType::BindingBand: return "Binding Band";
        case ItemType::ElectricSeed: return "Electric Seed";
        case ItemType::PsychicSeed: return "Psychic Seed";
        case ItemType::MistySeed: return "Misty Seed";
        case ItemType::GrassySeed: return "Grassy Seed";
        case ItemType::AdrenalineOrb: return "Adrenaline Orb";
        case ItemType::MicleBerry: return "Micle Berry";
        case ItemType::LansatBerry: return "Lansat Berry";
        case ItemType::StarfBerry: return "Starf Berry";
        case ItemType::ShedShell: return "Shed Shell";
        case ItemType::GripClaw: return "Grip Claw";
        case ItemType::IronBall: return "Iron Ball";
        case ItemType::AbsorbBulb: return "Absorb Bulb";
        case ItemType::CellBattery: return "Cell Battery";
        case ItemType::LuminousMoss: return "Luminous Moss";
        case ItemType::Snowball: return "Snowball";
        case ItemType::LaxIncense: return "Lax Incense";
        case ItemType::LaggingTail: return "Lagging Tail";
        case ItemType::RoseIncense: return "Rose Incense";
        case ItemType::WaveIncense: return "Wave Incense";
        case ItemType::OddIncense: return "Odd Incense";
        case ItemType::FloatStone: return "Float Stone";
        case ItemType::RazorClaw: return "Razor Claw";
        case ItemType::RazorFang: return "Razor Fang";
        case ItemType::FullIncense: return "Full Incense";
        case ItemType::SmokeBall: return "Smoke Ball";
        case ItemType::SoftSand: return "Soft Sand";
        case ItemType::DracoPlate: return "Draco Plate";
        case ItemType::DreadPlate: return "Dread Plate";
        case ItemType::RockIncense: return "Rock Incense";
        case ItemType::LuckIncense: return "Luck Incense";
        case ItemType::MachoBrace: return "Macho Brace";
        case ItemType::PowerBracer: return "Power Bracer";
        default: return "None";
    }
}

void initializeCoreItems(GameRegistry& registry) {
    // === Helper lambdas for group patterns (matching moves' factory lambda style) ===

    // Type boost items: 1.2x damage for moves of a specific type
    auto regTypeBoost = [&registry](ItemType type, Type boostedType) {
        registry.registerItem(type, [boostedType](Item& item) {
            item.setDamageModifier(1.2f, true, [boostedType](Pokemon*, Pokemon*, const Move& move) {
                return move.getType() == boostedType;
            });
        });
    };

    // Status cure berry: cures a specific status, then consumes
    auto regStatusBerry = [&registry](ItemType type, StatusType status) {
        registry.registerItem(type, [status](Item& item) {
            item.isConsumable = true;
            item.addEffect(ItemTrigger::OnStatus, [status](Pokemon* self, Pokemon*, BattleContext&, void*) {
                if (!self || !self->hasStatus(status)) return;
                self->removeStatus(status);
                self->removeItem();
            });
        });
    };

    // Half-HP heal berry: heals at <= 50% HP, then consumes
    auto regHalfHpHealBerry = [&registry](ItemType type, int numerator, int denominator) {
        registry.registerItem(type, [numerator, denominator](Item& item) {
            item.isConsumable = true;
            item.addEffect(ItemTrigger::OnDamage, [numerator, denominator](Pokemon* self, Pokemon*, BattleContext&, void*) {
                if (!self) return;
                if (self->getCurrentHP() > self->getMaxHP() / 2) return;
                int heal = std::max(1, self->getMaxHP() * numerator / denominator);
                self->setCurrentHP(self->getCurrentHP() + heal);
                self->removeItem();
            });
        });
    };

    // Resist berry: 0.5x damage from super-effective hits of a specific type, then consumes
    auto regResistBerry = [&registry](ItemType type, Type resistedType) {
        registry.registerItem(type, [resistedType](Item& item) {
            item.isConsumable = true;
            item.setDamageModifier(0.5f, false, [resistedType](Pokemon* self, Pokemon*, const Move& move) {
                if (!self || move.getType() != resistedType) return false;
                return self->getTypeEffectiveness(move.getType()) > 1.0f;
            });
            item.addEffect(ItemTrigger::OnDamage, [resistedType](Pokemon* self, Pokemon*, BattleContext&, void* context) {
                if (!self) return;
                const ItemDamageContext* dc = toDamageContext(context);
                if (!dc || !dc->move || dc->damage <= 0) return;
                if (dc->move->getType() != resistedType) return;
                if (!dc->wasSuperEffective) return;
                self->removeItem();
            });
        });
    };

    // Pinch stat berry: boosts a stat at <= 25% HP, then consumes
    auto regPinchBerry = [&registry](ItemType type, StatIndex stat) {
        registry.registerItem(type, [stat](Item& item) {
            item.isConsumable = true;
            item.addEffect(ItemTrigger::OnDamage, [stat](Pokemon* self, Pokemon*, BattleContext&, void*) {
                if (!self) return;
                if (self->getCurrentHP() > self->getMaxHP() / 4) return;
                self->changeStatStage(stat, 1);
                self->removeItem();
            });
        });
    };

    // Retaliation berry: damages attacker for 1/8 max HP, then consumes
    auto regRetaliationBerry = [&registry](ItemType type, Category triggerCategory) {
        registry.registerItem(type, [triggerCategory](Item& item) {
            item.isConsumable = true;
            item.addEffect(ItemTrigger::OnDamage, [triggerCategory](Pokemon* self, Pokemon* opponent, BattleContext&, void* context) {
                if (!self || !opponent) return;
                const ItemDamageContext* dc = toDamageContext(context);
                if (!dc || !dc->move || dc->damage <= 0) return;
                if (dc->move->getCategory() != triggerCategory) return;
                int reflectedDamage = std::max(1, opponent->getMaxHP() / 8);
                opponent->setCurrentHP(opponent->getCurrentHP() - reflectedDamage);
                self->removeItem();
            });
        });
    };

    // Choice items: stat modifier + OnEntry placeholder
    auto regChoiceItem = [&registry](ItemType type, ItemStatModifier::Stat stat, float mult) {
        registry.registerItem(type, [stat, mult](Item& item) {
            item.addEffect(ItemTrigger::OnEntry, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
                if (!self) return;
            });
            item.addStatModifier(stat, mult);
        });
    };

    // Terrain seed: boosts a stat on the matching terrain, then consumes
    auto regSeed = [&registry](ItemType type, FieldType fieldType, StatIndex stat) {
        registry.registerItem(type, [fieldType, stat](Item& item) {
            item.isConsumable = true;
            item.addEffect(ItemTrigger::OnEntry, [fieldType, stat](Pokemon* self, Pokemon*, BattleContext& ctx, void*) {
                if (self && ctx.getField().type == fieldType) { self->changeStatStage(stat, 1); self->removeItem(); }
            });
        });
    };

    // Weather rock: extends weather duration
    auto regWeatherRock = [&registry](ItemType type) {
        registry.registerItem(type, [](Item& item) {
            item.passive.extendsWeather = true;
        });
    };

    // Passive-only items: just set passive flags
    auto regPassive = [&registry](ItemType type, std::function<void(Item::ItemPassiveFlags&)> setFlags) {
        registry.registerItem(type, [setFlags](Item& item) {
            setFlags(item.passive);
        });
    };

    // Consumable + passive items
    auto regConsumablePassive = [&registry](ItemType type, std::function<void(Item::ItemPassiveFlags&)> setFlags) {
        registry.registerItem(type, [setFlags](Item& item) {
            item.isConsumable = true;
            setFlags(item.passive);
        });
    };

    // ================================================================
    // === Standalone items (each with unique logic) ===
    // ================================================================

    registry.registerItem(ItemType::OranBerry, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            if (self->getCurrentHP() <= self->getMaxHP() / 2) {
                self->setCurrentHP(self->getCurrentHP() + 10);
                self->removeItem();
            }
        });
    });

    registry.registerItem(ItemType::SitrusBerry, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            if (self->getCurrentHP() <= self->getMaxHP() / 2) {
                int heal = std::max(1, self->getMaxHP() / 4);
                self->setCurrentHP(self->getCurrentHP() + heal);
                self->removeItem();
            }
        });
    });

    registry.registerItem(ItemType::LumBerry, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnStatus, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            self->clearStatuses();
            self->removeItem();
        });
    });

    registry.registerItem(ItemType::Leftovers, [](Item& item) {
        item.addEffect(ItemTrigger::OnTurnEnd, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            int heal = std::max(1, self->getMaxHP() / 16);
            self->setCurrentHP(self->getCurrentHP() + heal);
        });
    });

    registry.registerItem(ItemType::LifeOrb, [](Item& item) {
        item.addEffect(ItemTrigger::OnDealDamage, [](Pokemon* self, Pokemon*, BattleContext&, void* context) {
            if (!self) return;
            const ItemDamageContext* dc = toDamageContext(context);
            if (!tookDamageFromDamagingMove(dc)) return;
            int recoil = std::max(1, self->getMaxHP() / 10);
            self->setCurrentHP(self->getCurrentHP() - recoil);
        });
        item.setDamageModifier(1.3f, true);
    });

    registry.registerItem(ItemType::FocusSash, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon*, BattleContext&, void* context) {
            if (!self) return;
            const ItemDamageContext* dc = toDamageContext(context);
            if (!dc || !dc->isDamagingMove) return;
            if (dc->hpBeforeDamage >= self->getMaxHP() && self->getCurrentHP() <= 0) {
                self->setCurrentHP(1);
                self->removeItem();
            }
        });
    });

    registry.registerItem(ItemType::RockyHelmet, [](Item& item) {
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon* opponent, BattleContext&, void* context) {
            if (!self || !opponent) return;
            const ItemDamageContext* dc = toDamageContext(context);
            if (!dc || !dc->isContact || dc->damage <= 0) return;
            int reflectedDamage = std::max(1, opponent->getMaxHP() / 6);
            opponent->setCurrentHP(opponent->getCurrentHP() - reflectedDamage);
        });
    });

    registry.registerItem(ItemType::AirBalloon, [](Item& item) {
        item.isConsumable = true;
        item.setDamageModifier(0.0f, false, [](Pokemon* self, Pokemon*, const Move& move) {
            return self && move.getType() == Type::Ground;
        });
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon*, BattleContext&, void* context) {
            if (!self) return;
            const ItemDamageContext* dc = toDamageContext(context);
            if (tookDamageFromDamagingMove(dc)) self->removeItem();
        });
    });

    registry.registerItem(ItemType::Eviolite, [](Item& item) {
        item.addEffect(ItemTrigger::OnEntry, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
        });
        item.addStatModifier(ItemStatModifier::Stat::Defense, 1.5f);
        item.addStatModifier(ItemStatModifier::Stat::SpDefense, 1.5f);
    });

    registry.registerItem(ItemType::AssaultVest, [](Item& item) {
        item.addEffect(ItemTrigger::OnEntry, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
        });
        item.addStatModifier(ItemStatModifier::Stat::SpDefense, 1.5f);
    });

    registry.registerItem(ItemType::RedCard, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon* opponent, BattleContext& ctx, void* context) {
            if (!self || !opponent) return;
            const ItemDamageContext* dc = toDamageContext(context);
            if (!tookDamageFromDamagingMove(dc) || self->isFainted()) return;
            Side* opponentSide = ctx.findSideForPokemon(opponent);
            if (opponentSide) {
                opponentSide->autoSwitchNext();
                self->removeItem();
            }
        });
    });

    registry.registerItem(ItemType::WeaknessPolicy, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon*, BattleContext&, void* context) {
            if (!self) return;
            const ItemDamageContext* dc = toDamageContext(context);
            if (!dc || !dc->wasSuperEffective || dc->damage <= 0) return;
            self->changeStatStage(StatIndex::Attack, 2);
            self->changeStatStage(StatIndex::SpecialAttack, 2);
            self->removeItem();
        });
    });

    registry.registerItem(ItemType::BlackSludge, [](Item& item) {
        item.addEffect(ItemTrigger::OnTurnEnd, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            bool isPoisonType = (self->getType1() == Type::Poison || self->getType2() == Type::Poison);
            if (isPoisonType) {
                int heal = std::max(1, self->getMaxHP() / 16);
                self->setCurrentHP(self->getCurrentHP() + heal);
            } else {
                int damage = self->getMaxHP() / 8;
                self->setCurrentHP(self->getCurrentHP() - damage);
            }
        });
    });

    registry.registerItem(ItemType::ShellBell, [](Item& item) {
        item.addEffect(ItemTrigger::OnDealDamage, [](Pokemon* self, Pokemon*, BattleContext&, void* context) {
            if (!self) return;
            const ItemDamageContext* dc = toDamageContext(context);
            if (!tookDamageFromDamagingMove(dc)) return;
            int heal = dc->damage / 8;
            if (heal > 0) self->setCurrentHP(self->getCurrentHP() + heal);
        });
    });

    registry.registerItem(ItemType::ExpertBelt, [](Item& item) {
        item.setDamageModifier(1.2f, true, [](Pokemon* self, Pokemon* opponent, const Move& move) {
            if (!self || !opponent) return false;
            return opponent->getTypeEffectiveness(move.getType()) > 1.0f;
        });
    });

    registry.registerItem(ItemType::MuscleBand, [](Item& item) {
        item.addStatModifier(ItemStatModifier::Stat::Attack, 1.1f);
    });

    registry.registerItem(ItemType::WiseGlasses, [](Item& item) {
        item.addStatModifier(ItemStatModifier::Stat::SpAttack, 1.1f);
    });

    registry.registerItem(ItemType::LightBall, [](Item& item) {
        item.addStatModifier(ItemStatModifier::Stat::Attack, 2.0f);
        item.addStatModifier(ItemStatModifier::Stat::SpAttack, 2.0f);
    });

    registry.registerItem(ItemType::QuickPowder, [](Item& item) {
        item.addStatModifier(ItemStatModifier::Stat::Speed, 2.0f);
    });

    registry.registerItem(ItemType::ThickClub, [](Item& item) {
        item.addStatModifier(ItemStatModifier::Stat::Attack, 2.0f);
    });

    registry.registerItem(ItemType::MetalPowder, [](Item& item) {
        item.addStatModifier(ItemStatModifier::Stat::Defense, 1.5f);
        item.addStatModifier(ItemStatModifier::Stat::SpDefense, 1.5f);
    });

    registry.registerItem(ItemType::DeepSeaTooth, [](Item& item) {
        item.addStatModifier(ItemStatModifier::Stat::SpAttack, 2.0f);
    });

    registry.registerItem(ItemType::DeepSeaScale, [](Item& item) {
        item.addStatModifier(ItemStatModifier::Stat::SpDefense, 2.0f);
    });

    registry.registerItem(ItemType::PowerHerb, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnAttack, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (self) self->removeItem();
        });
        item.addEffect(ItemTrigger::OnDealDamage, [](Pokemon* self, Pokemon*, BattleContext&, void* context) {
            if (!self) return;
            const ItemDamageContext* dc = toDamageContext(context);
            if (!dc || !dc->move) return;
            if (dc->move->getName() == "Fly" || dc->move->getName() == "Protect") self->removeItem();
        });
    });

    registry.registerItem(ItemType::StickyBarb, [](Item& item) {
        item.addEffect(ItemTrigger::OnTurnEnd, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            int damage = std::max(1, self->getMaxHP() / 8);
            self->setCurrentHP(self->getCurrentHP() - damage);
        });
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon* opponent, BattleContext&, void* context) {
            if (!self || !opponent) return;
            const ItemDamageContext* dc = toDamageContext(context);
            if (!dc || !dc->isContact || dc->damage <= 0) return;
            int damage = std::max(1, opponent->getMaxHP() / 8);
            opponent->setCurrentHP(opponent->getCurrentHP() - damage);
        });
    });

    registry.registerItem(ItemType::BigRoot, [](Item& item) {
        item.addEffect(ItemTrigger::OnDealDamage, [](Pokemon* self, Pokemon*, BattleContext&, void* context) {
            if (!self) return;
            const ItemDamageContext* dc = toDamageContext(context);
            if (!dc || dc->damage <= 0) return;
            int heal = std::max(1, dc->damage * 3 / 10);
            self->setCurrentHP(self->getCurrentHP() + heal);
        });
    });

    registry.registerItem(ItemType::KingsRock, [](Item& item) {
        item.addEffect(ItemTrigger::OnDealDamage, [](Pokemon* self, Pokemon* opponent, BattleContext&, void* context) {
            if (!self || !opponent) return;
            const ItemDamageContext* dc = toDamageContext(context);
            if (!dc || !dc->isDamagingMove || dc->damage <= 0) return;
            if (!dc->move || dc->move->getEffect() == MoveEffect::Flinch) return;
            if (opponent->getAbility() == AbilityType::InnerFocus) return;
            if (PRNG::nextInt(0, 100) < 10) opponent->addStatus(StatusType::Flinch, 1);
        });
    });

    registry.registerItem(ItemType::WideLens, [](Item& item) {
        item.addStatModifier(ItemStatModifier::Stat::Accuracy, 1.1f);
    });

    registry.registerItem(ItemType::ZoomLens, [](Item& item) {
        item.addStatModifier(ItemStatModifier::Stat::Accuracy, 1.2f);
    });

    registry.registerItem(ItemType::ScopeLens, [](Item& item) {
        item.addStatModifier(ItemStatModifier::Stat::Accuracy, 1.1f);
    });

    registry.registerItem(ItemType::FlameOrb, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnTurnEnd, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (self && !self->hasStatus(StatusType::Burn)) {
                self->addStatus(StatusType::Burn);
                self->removeItem();
            }
        });
    });

    registry.registerItem(ItemType::ToxicOrb, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnTurnEnd, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (self && !self->hasStatus(StatusType::ToxicPoison)) {
                self->addStatus(StatusType::ToxicPoison);
                self->removeItem();
            }
        });
    });

    registry.registerItem(ItemType::EjectButton, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon*, BattleContext& ctx, void* context) {
            if (!self) return;
            const ItemDamageContext* dc = toDamageContext(context);
            if (!tookDamageFromDamagingMove(dc) || self->isFainted()) return;
            Side* selfSide = ctx.findSideForPokemon(self);
            if (selfSide) {
                selfSide->autoSwitchNext();
                self->removeItem();
            }
        });
    });

    registry.registerItem(ItemType::WhiteHerb, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnStatChange, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            const StatIndex stats[] = {StatIndex::Attack, StatIndex::Defense, StatIndex::SpecialAttack, StatIndex::SpecialDefense, StatIndex::Speed};
            bool restored = false;
            for (StatIndex stat : stats) {
                const int stage = self->getStatStage(stat);
                if (stage < 0) { self->changeStatStage(stat, -stage); restored = true; }
            }
            if (restored) self->removeItem();
        });
    });

    registry.registerItem(ItemType::BerryJuice, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            if (self->getCurrentHP() <= self->getMaxHP() / 2) {
                self->setCurrentHP(self->getCurrentHP() + 20);
                self->removeItem();
            }
        });
    });

    registry.registerItem(ItemType::PunchingGlove, [](Item& item) {
        item.passive.preventsContactEffects = true;
        item.setDamageModifier(1.1f, true, [](Pokemon*, Pokemon*, const Move& move) -> bool {
            const std::string key = [&move]() {
                std::string n;
                for (char ch : move.getName()) {
                    if (ch == ' ' || ch == '-' || ch == '\'') continue;
                    n.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
                }
                return n;
            }();
            return key == "bulletpunch" || key == "cometpunch" || key == "dizzypunch"
                || key == "doubleironbash" || key == "drainpunch" || key == "dynamicpunch"
                || key == "firepunch" || key == "focuspunch" || key == "hammerarm"
                || key == "icehammer" || key == "icepunch" || key == "jetpunch"
                || key == "machpunch" || key == "megapunch" || key == "meteormash"
                || key == "plasmafists" || key == "poweruppunch" || key == "ragefist"
                || key == "shadowpunch" || key == "skydrop" || key == "suckerpunch"
                || key == "thunderpunch" || key == "triplearrows";
        });
    });

    registry.registerItem(ItemType::BoosterEnergy, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnEntry, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            const AbilityType ability = self->getAbility();
            if (ability != AbilityType::Protosynthesis && ability != AbilityType::QuarkDrive) return;
            if (self->isParadoxActive()) return;
            self->setParadoxActive(true);
            self->removeItem();
        });
    });

    registry.registerItem(ItemType::MirrorHerb, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnStatChange, [](Pokemon* self, Pokemon* opponent, BattleContext&, void*) {
            if (!self || !opponent || self == opponent) return;
            constexpr StatIndex kStats[] = {StatIndex::Attack, StatIndex::Defense, StatIndex::SpecialAttack, StatIndex::SpecialDefense, StatIndex::Speed};
            bool copied = false;
            for (StatIndex idx : kStats) {
                const int oppStage = opponent->getStatStage(idx);
                if (oppStage > 0) {
                    const int selfStage = self->getStatStage(idx);
                    const int delta = oppStage - selfStage;
                    if (delta > 0) { self->changeStatStage(idx, delta); copied = true; }
                }
            }
            if (copied) self->removeItem();
        });
    });

    registry.registerItem(ItemType::EjectPack, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnStatChange, [](Pokemon* self, Pokemon*, BattleContext& ctx, void*) {
            if (!self || self->isFainted()) return;
            constexpr StatIndex kStats[] = {StatIndex::Attack, StatIndex::Defense, StatIndex::SpecialAttack, StatIndex::SpecialDefense, StatIndex::Speed};
            bool lowered = false;
            for (StatIndex idx : kStats) { if (self->getStatStage(idx) < 0) { lowered = true; break; } }
            if (lowered) {
                Side* selfSide = ctx.findSideForPokemon(self);
                if (selfSide && selfSide->canSwitch()) { selfSide->autoSwitchNext(); self->removeItem(); }
            }
        });
    });

    registry.registerItem(ItemType::RoomService, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnEntry, [](Pokemon* self, Pokemon*, BattleContext& ctx, void*) {
            if (self && ctx.getField().isTrickRoom()) { self->changeStatStage(StatIndex::Speed, -1); self->removeItem(); }
        });
    });

    registry.registerItem(ItemType::BlunderPolicy, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::AfterMoveMiss, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (self) { self->changeStatStage(StatIndex::Speed, 2); self->removeItem(); }
        });
    });

    registry.registerItem(ItemType::ThroatSpray, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::AfterSoundMove, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (self) { self->changeStatStage(StatIndex::SpecialAttack, 1); self->removeItem(); }
        });
    });

    registry.registerItem(ItemType::MentalHerb, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnStatus, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            self->removeItem();
        });
    });

    registry.registerItem(ItemType::RingTarget, [](Item&) {
        // Ring Target removes type-based immunities for the holder
        // Checked in type effectiveness calculation
    });

    registry.registerItem(ItemType::Metronome, [](Item&) {
        // Metronome boosts consecutive uses of the same move
        // Checked during damage calculation based on consecutive use count
    });

    registry.registerItem(ItemType::MicleBerry, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (self && self->getCurrentHP() > 0 && self->getCurrentHP() <= self->getMaxHP() / 4) { self->changeAccuracyStage(1); self->removeItem(); }
        });
    });

    registry.registerItem(ItemType::LansatBerry, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon*, BattleContext& ctx, void*) {
            if (self && self->getCurrentHP() > 0 && self->getCurrentHP() <= self->getMaxHP() / 4) { ctx.getRuntimeMoveState().criticalHitStage[self] = std::min(4, ctx.getRuntimeMoveState().criticalHitStage[self] + 2); self->removeItem(); }
        });
    });

    registry.registerItem(ItemType::StarfBerry, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self || self->getCurrentHP() <= 0 || self->getCurrentHP() > self->getMaxHP() / 4) return;
            constexpr StatIndex kStats[] = {StatIndex::Attack, StatIndex::Defense, StatIndex::SpecialAttack, StatIndex::SpecialDefense, StatIndex::Speed};
            int idx = static_cast<int>(PRNG::nextFloat(0.0f, 5.0f));
            self->changeStatStage(kStats[std::min(4, idx)], 2);
            self->removeItem();
        });
    });

    registry.registerItem(ItemType::AbsorbBulb, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon*, BattleContext&, void* context) {
            const ItemDamageContext* dc = toDamageContext(context);
            if (dc && dc->move && dc->move->getType() == Type::Water && dc->damage > 0) { self->changeStatStage(StatIndex::SpecialAttack, 1); self->removeItem(); }
        });
    });

    registry.registerItem(ItemType::CellBattery, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon*, BattleContext&, void* context) {
            const ItemDamageContext* dc = toDamageContext(context);
            if (dc && dc->move && dc->move->getType() == Type::Electric && dc->damage > 0) { self->changeStatStage(StatIndex::Attack, 1); self->removeItem(); }
        });
    });

    registry.registerItem(ItemType::LuminousMoss, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon*, BattleContext&, void* context) {
            const ItemDamageContext* dc = toDamageContext(context);
            if (dc && dc->move && dc->move->getType() == Type::Water && dc->damage > 0) { self->changeStatStage(StatIndex::SpecialDefense, 1); self->removeItem(); }
        });
    });

    registry.registerItem(ItemType::Snowball, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnDamage, [](Pokemon* self, Pokemon*, BattleContext&, void* context) {
            const ItemDamageContext* dc = toDamageContext(context);
            if (dc && dc->move && dc->move->getType() == Type::Ice && dc->damage > 0) { self->changeStatStage(StatIndex::Attack, 1); self->removeItem(); }
        });
    });

    registry.registerItem(ItemType::ChestoBerry, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnStatus, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            if (self->hasStatus(StatusType::Sleep)) { self->removeStatus(StatusType::Sleep); self->removeItem(); }
        });
    });

    registry.registerItem(ItemType::PechaBerry, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnStatus, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            if (self->hasStatus(StatusType::Poison) || self->hasStatus(StatusType::ToxicPoison)) {
                self->removeStatus(StatusType::Poison);
                self->removeStatus(StatusType::ToxicPoison);
                self->removeItem();
            }
        });
    });

    registry.registerItem(ItemType::RawstBerry, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnStatus, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            if (self->hasStatus(StatusType::Burn)) { self->removeStatus(StatusType::Burn); self->removeItem(); }
        });
    });

    registry.registerItem(ItemType::AspearBerry, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnStatus, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            if (self->hasStatus(StatusType::Freeze)) { self->removeStatus(StatusType::Freeze); self->removeItem(); }
        });
    });

    registry.registerItem(ItemType::PersimBerry, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnStatus, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (!self) return;
            if (self->hasStatus(StatusType::Confusion)) { self->removeStatus(StatusType::Confusion); self->removeItem(); }
        });
    });

    // === Simple passive flag items ===
    regPassive(ItemType::QuickClaw, [](auto& p) { p.hasQuickClaw = true; });
    regPassive(ItemType::HeavyDutyBoots, [](auto& p) { p.blocksEntryHazards = true; });
    regPassive(ItemType::CovertCloak, [](auto& p) { p.blocksSecondaryEffects = true; });
    regPassive(ItemType::ClearAmulet, [](auto& p) { p.preventsStatDrops = true; });
    regPassive(ItemType::ProtectivePads, [](auto& p) { p.preventsContactEffects = true; });
    regPassive(ItemType::LoadedDice, [](auto& p) { p.maximizesMultiHit = true; });
    regPassive(ItemType::AbilityShield, [](auto& p) { p.blocksAbilityChange = true; });
    regPassive(ItemType::TerrainExtender, [](auto& p) { p.extendsTerrain = true; });
    regPassive(ItemType::UtilityUmbrella, [](auto& p) { p.ignoresWeather = true; });
    regPassive(ItemType::LightClay, [](auto& p) { p.extendsScreens = true; });
    regPassive(ItemType::SafetyGoggles, [](auto& p) { p.blocksWeatherPowder = true; });
    regPassive(ItemType::BrightPowder, [](auto& p) { p.evasionBoost = 1.111f; });
    regPassive(ItemType::FocusBand, [](auto& p) { p.hasFocusBand = true; });
    regPassive(ItemType::BindingBand, [](auto& p) { p.boostsBindingMoves = true; });
    regPassive(ItemType::ShedShell, [](auto& p) { p.ensuresCanSwitch = true; });
    regPassive(ItemType::GripClaw, [](auto& p) { p.extendsTrappingMoves = true; });
    regPassive(ItemType::IronBall, [](auto& p) { p.halvesSpeedAndGrounds = true; });
    regPassive(ItemType::LaxIncense, [](auto& p) { p.evasionBoost = 1.05f; });
    regPassive(ItemType::LaggingTail, [](auto& p) { p.alwaysMovesLast = true; });
    regPassive(ItemType::FloatStone, [](auto& p) { p.halvesWeight = true; });
    regPassive(ItemType::RazorClaw, [](auto& p) { p.critStageBoost = true; });
    regPassive(ItemType::RazorFang, [](auto& p) { p.flinchOnHit = true; });
    regPassive(ItemType::FullIncense, [](auto& p) { p.alwaysMovesLast = true; });
    regPassive(ItemType::MachoBrace, [](auto& p) { p.alwaysMovesLast = true; });
    regPassive(ItemType::PowerBracer, [](auto& p) { p.alwaysMovesLast = true; });

    // === Consumable + passive items ===
    regConsumablePassive(ItemType::CustapBerry, [](auto& p) { p.hasCustapBerry = true; });
    regConsumablePassive(ItemType::EnigmaBerry, [](auto& p) { p.healsOnSuperEffective = true; });

    // === No-op items (no modifications needed) ===
    registry.registerItem(ItemType::SmokeBall, [](Item&) {});
    registry.registerItem(ItemType::LuckIncense, [](Item&) {});

    // === Items with stat modifiers via direct push_back ===
    registry.registerItem(ItemType::RoseIncense, [](Item& item) {
        item.statModifiers.push_back({ItemStatModifier::Stat::SpAttack, 1.2f});
    });
    registry.registerItem(ItemType::WaveIncense, [](Item& item) {
        item.statModifiers.push_back({ItemStatModifier::Stat::SpAttack, 1.2f});
    });
    registry.registerItem(ItemType::OddIncense, [](Item& item) {
        item.statModifiers.push_back({ItemStatModifier::Stat::SpAttack, 1.2f});
    });
    registry.registerItem(ItemType::SoftSand, [](Item& item) {
        item.statModifiers.push_back({ItemStatModifier::Stat::SpAttack, 1.2f});
    });
    registry.registerItem(ItemType::DracoPlate, [](Item& item) {
        item.statModifiers.push_back({ItemStatModifier::Stat::SpAttack, 1.2f});
    });
    registry.registerItem(ItemType::DreadPlate, [](Item& item) {
        item.statModifiers.push_back({ItemStatModifier::Stat::SpAttack, 1.2f});
    });
    registry.registerItem(ItemType::RockIncense, [](Item& item) {
        item.statModifiers.push_back({ItemStatModifier::Stat::SpAttack, 1.2f});
    });

    registry.registerItem(ItemType::AdrenalineOrb, [](Item& item) {
        item.isConsumable = true;
        item.addEffect(ItemTrigger::OnStatChange, [](Pokemon* self, Pokemon*, BattleContext&, void*) {
            if (self && self->getStatStage(StatIndex::Speed) > 0) self->removeItem();
        });
    });

    // ================================================================
    // === Group-driven registrations ===
    // ================================================================

    // Choice items
    regChoiceItem(ItemType::ChoiceBand, ItemStatModifier::Stat::Attack, 1.5f);
    regChoiceItem(ItemType::ChoiceSpecs, ItemStatModifier::Stat::SpAttack, 1.5f);
    regChoiceItem(ItemType::ChoiceScarf, ItemStatModifier::Stat::Speed, 1.5f);

    // Type boost items
    regTypeBoost(ItemType::SilverPowder, Type::Bug);
    regTypeBoost(ItemType::MetalCoat, Type::Steel);
    regTypeBoost(ItemType::HardStone, Type::Rock);
    regTypeBoost(ItemType::MiracleSeed, Type::Grass);
    regTypeBoost(ItemType::BlackGlasses, Type::Dark);
    regTypeBoost(ItemType::BlackBelt, Type::Fighting);
    regTypeBoost(ItemType::Magnet, Type::Electric);
    regTypeBoost(ItemType::MysticWater, Type::Water);
    regTypeBoost(ItemType::SharpBeak, Type::Flying);
    regTypeBoost(ItemType::PoisonBarb, Type::Poison);
    regTypeBoost(ItemType::NeverMeltIce, Type::Ice);
    regTypeBoost(ItemType::SpellTag, Type::Ghost);
    regTypeBoost(ItemType::TwistedSpoon, Type::Psychic);
    regTypeBoost(ItemType::Charcoal, Type::Fire);
    regTypeBoost(ItemType::DragonFang, Type::Dragon);
    regTypeBoost(ItemType::SilkScarf, Type::Normal);
    regTypeBoost(ItemType::SeaIncense, Type::Water);

    // Type plates
    regTypeBoost(ItemType::FlamePlate, Type::Fire);
    regTypeBoost(ItemType::SplashPlate, Type::Water);
    regTypeBoost(ItemType::ZapPlate, Type::Electric);
    regTypeBoost(ItemType::MeadowPlate, Type::Grass);
    regTypeBoost(ItemType::IciclePlate, Type::Ice);
    regTypeBoost(ItemType::FistPlate, Type::Fighting);
    regTypeBoost(ItemType::ToxicPlate, Type::Poison);
    regTypeBoost(ItemType::EarthPlate, Type::Ground);
    regTypeBoost(ItemType::SkyPlate, Type::Flying);
    regTypeBoost(ItemType::MindPlate, Type::Psychic);
    regTypeBoost(ItemType::InsectPlate, Type::Bug);
    regTypeBoost(ItemType::StonePlate, Type::Rock);
    regTypeBoost(ItemType::SpookyPlate, Type::Ghost);
    regTypeBoost(ItemType::IronPlate, Type::Steel);

    // Status cure berries
    regStatusBerry(ItemType::CheriBerry, StatusType::Paralysis);

    // Half-HP heal berries
    regHalfHpHealBerry(ItemType::FigyBerry, 1, 8);
    regHalfHpHealBerry(ItemType::WikiBerry, 1, 8);
    regHalfHpHealBerry(ItemType::MagoBerry, 1, 8);
    regHalfHpHealBerry(ItemType::AguavBerry, 1, 8);
    regHalfHpHealBerry(ItemType::IapapaBerry, 1, 8);

    // Resist berries
    regResistBerry(ItemType::OccaBerry, Type::Fire);
    regResistBerry(ItemType::PasshoBerry, Type::Water);
    regResistBerry(ItemType::WacanBerry, Type::Electric);
    regResistBerry(ItemType::RindoBerry, Type::Grass);
    regResistBerry(ItemType::YacheBerry, Type::Ice);
    regResistBerry(ItemType::ChopleBerry, Type::Fighting);
    regResistBerry(ItemType::KebiaBerry, Type::Poison);
    regResistBerry(ItemType::ShucaBerry, Type::Ground);
    regResistBerry(ItemType::CobaBerry, Type::Flying);
    regResistBerry(ItemType::PayapaBerry, Type::Psychic);
    regResistBerry(ItemType::TangaBerry, Type::Bug);
    regResistBerry(ItemType::ChartiBerry, Type::Rock);
    regResistBerry(ItemType::KasibBerry, Type::Ghost);
    regResistBerry(ItemType::HabanBerry, Type::Dragon);
    regResistBerry(ItemType::ColburBerry, Type::Dark);
    regResistBerry(ItemType::BabiriBerry, Type::Steel);
    regResistBerry(ItemType::ChilanBerry, Type::Normal);

    // Pinch stat berries
    regPinchBerry(ItemType::LiechiBerry, StatIndex::Attack);
    regPinchBerry(ItemType::GanlonBerry, StatIndex::Defense);
    regPinchBerry(ItemType::SalacBerry, StatIndex::Speed);
    regPinchBerry(ItemType::PetayaBerry, StatIndex::SpecialAttack);
    regPinchBerry(ItemType::ApicotBerry, StatIndex::SpecialDefense);

    // Retaliation berries
    regRetaliationBerry(ItemType::JabocaBerry, Category::Physical);
    regRetaliationBerry(ItemType::RowapBerry, Category::Special);

    // Terrain seeds
    regSeed(ItemType::ElectricSeed, FieldType::Electric, StatIndex::Defense);
    regSeed(ItemType::PsychicSeed, FieldType::Psychic, StatIndex::SpecialDefense);
    regSeed(ItemType::MistySeed, FieldType::Misty, StatIndex::SpecialDefense);
    regSeed(ItemType::GrassySeed, FieldType::Grassy, StatIndex::Defense);

    // Weather rocks
    regWeatherRock(ItemType::DampRock);
    regWeatherRock(ItemType::HeatRock);
    regWeatherRock(ItemType::IcyRock);
    regWeatherRock(ItemType::SmoothRock);
}

bool isBerry(ItemType type) {
    switch (type) {
        case ItemType::OranBerry:
        case ItemType::SitrusBerry:
        case ItemType::LumBerry:
        case ItemType::ChestoBerry:
        case ItemType::PechaBerry:
        case ItemType::RawstBerry:
        case ItemType::AspearBerry:
        case ItemType::PersimBerry:
        case ItemType::CheriBerry:
        case ItemType::FigyBerry:
        case ItemType::WikiBerry:
        case ItemType::MagoBerry:
        case ItemType::AguavBerry:
        case ItemType::IapapaBerry:
        case ItemType::OccaBerry:
        case ItemType::PasshoBerry:
        case ItemType::WacanBerry:
        case ItemType::RindoBerry:
        case ItemType::YacheBerry:
        case ItemType::ChopleBerry:
        case ItemType::KebiaBerry:
        case ItemType::ShucaBerry:
        case ItemType::CobaBerry:
        case ItemType::PayapaBerry:
        case ItemType::TangaBerry:
        case ItemType::ChartiBerry:
        case ItemType::KasibBerry:
        case ItemType::HabanBerry:
        case ItemType::ColburBerry:
        case ItemType::BabiriBerry:
        case ItemType::ChilanBerry:
        case ItemType::LiechiBerry:
        case ItemType::GanlonBerry:
        case ItemType::SalacBerry:
        case ItemType::PetayaBerry:
        case ItemType::ApicotBerry:
        case ItemType::JabocaBerry:
        case ItemType::RowapBerry:
            return true;
        default:
            return false;
    }
}

void Item::executeTrigger(ItemTrigger trigger, Pokemon* self, Pokemon* opponent, BattleContext& ctx, void* context) const {
    if (isUsed && isConsumable) return;

    auto it = effects.find(trigger);
    if (it != effects.end() && it->second) {
        it->second(self, opponent, ctx, context);
    }
}

// === Item logic helpers ===

bool itemPreventsStatDrops(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.preventsStatDrops;
}

bool itemPreventsContact(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.preventsContactEffects;
}

bool itemBlocksEntryHazards(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.blocksEntryHazards;
}

bool itemBlocksSecondaryEffects(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.blocksSecondaryEffects;
}

bool itemMaximizesMultiHit(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.maximizesMultiHit;
}

bool itemBlocksAbilityChange(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.blocksAbilityChange;
}

bool itemExtendsTerrain(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.extendsTerrain;
}

bool itemIgnoresWeather(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.ignoresWeather;
}

bool itemExtendsScreens(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.extendsScreens;
}

bool itemBlocksWeatherPowder(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.blocksWeatherPowder;
}

bool itemExtendsWeather(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.extendsWeather;
}

bool itemHasFocusBand(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.hasFocusBand;
}

bool itemHasCustapBerry(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.hasCustapBerry;
}

float itemEvasionBoost(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.evasionBoost;
}

bool itemHealsOnSuperEffective(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.healsOnSuperEffective;
}

bool itemBoostsBindingMoves(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.boostsBindingMoves;
}

bool itemExtendsTrappingMoves(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.extendsTrappingMoves;
}

bool itemEnsuresCanSwitch(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.ensuresCanSwitch;
}

bool itemHalvesSpeedAndGrounds(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.halvesSpeedAndGrounds;
}

bool itemAlwaysMovesLast(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.alwaysMovesLast;
}

bool itemHalvesWeight(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.halvesWeight;
}

bool itemCritStageBoost(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.critStageBoost;
}

bool itemFlinchOnHit(ItemType type) {
    return GameRegistry::instance().getItem(type).passive.flinchOnHit;
}

bool tryQuickClawActivation(ItemType type, int& priority) {
    if (type != ItemType::QuickClaw) return false;
    if (PRNG::nextFloat(0.0f, 1.0f) < 0.2f) {
        priority = std::numeric_limits<int>::max() / 4;
        return true;
    }
    return false;
}

float knockOffDamageMultiplier(const Move& move, ItemType targetItemType) {
    // normalize token check
    const std::string& name = move.getName();
    std::string normalized;
    normalized.reserve(name.size());
    for (char ch : name) {
        if (ch == ' ' || ch == '-' || ch == '\'' || ch == '_') continue;
        normalized.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
    }
    if (normalized == "knockoff" && targetItemType != ItemType::None) {
        return 1.5f;
    }
    return 1.0f;
}

bool tryKnockOffItemRemoval(const Move& move, Pokemon* defender) {
    if (!defender) return false;
    const std::string& name = move.getName();
    std::string normalized;
    normalized.reserve(name.size());
    for (char ch : name) {
        if (ch == ' ' || ch == '-' || ch == '\'' || ch == '_') continue;
        normalized.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
    }
    if (normalized != "knockoff") return false;
    if (defender->getItemType() != ItemType::None) {
        defender->removeItem();
    }
    return true;  // Knock Off always stops further processing
}
