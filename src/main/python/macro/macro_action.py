# SPDX-License-Identifier: GPL-2.0-or-later
import base64
import struct

from keycodes.keycodes import Keycode
from protocol.constants import VIAL_PROTOCOL_ADVANCED_MACROS

SS_QMK_PREFIX = 1

SS_TAP_CODE = 1
SS_DOWN_CODE = 2
SS_UP_CODE = 3
SS_DELAY_CODE = 4
VIAL_MACRO_EXT_TAP = 5
VIAL_MACRO_EXT_DOWN = 6
VIAL_MACRO_EXT_UP = 7
SS_PASSWORD_CODE = 8


class BasicAction:

    tag = "unknown"

    def save(self):
        return [self.tag]

    def restore(self, act):
        if self.tag != act[0]:
            raise RuntimeError("cannot restore {}: expected tag={} got tag={}".format(
                self, self.tag, act[0]
            ))

    def __eq__(self, other):
        return self.tag == other.tag


class ActionText(BasicAction):

    tag = "text"

    def __init__(self, text=""):
        super().__init__()
        self.text = text

    def serialize(self, vial_protocol):
        return self.text.encode("utf-8")

    def save(self):
        return super().save() + [self.text]

    def restore(self, act):
        super().restore(act)
        self.text = act[1]

    def __eq__(self, other):
        return super().__eq__(other) and self.text == other.text

    def __repr__(self):
        return "{}<{}>".format(self.tag, self.text)


class ActionSequence(BasicAction):

    tag = "unknown-sequence"

    def __init__(self, sequence=None):
        super().__init__()
        if sequence is None:
            sequence = []
        self.sequence = sequence

    def serialize_prefix(self, kc):
        raise NotImplementedError

    def serialize(self, vial_protocol):
        out = b""
        for kc in self.sequence:
            if vial_protocol >= VIAL_PROTOCOL_ADVANCED_MACROS:
                out += struct.pack("B", SS_QMK_PREFIX)
            kc = Keycode.deserialize(kc)
            out += self.serialize_prefix(kc)
            if kc < 256:
                out += struct.pack("B", kc)
            else:
                # see decode_keycode() in qmk
                if kc % 256 == 0:
                    kc = 0xFF00 | (kc >> 8)
                out += struct.pack("<H", kc)
        return out

    def save(self):
        out = super().save()
        for kc in self.sequence:
            out.append(kc)
        return out

    def restore(self, act):
        super().restore(act)
        for kc in act[1:]:
            self.sequence.append(kc)

    def __eq__(self, other):
        return super().__eq__(other) and self.sequence == other.sequence

    def __repr__(self):
        return "{}<{}>".format(self.tag, self.sequence)


class ActionDown(ActionSequence):

    tag = "down"

    def serialize_prefix(self, kc):
        if kc >= 256:
            return b"\x06"
        return b"\x02"


class ActionUp(ActionSequence):

    tag = "up"

    def serialize_prefix(self, kc):
        if kc >= 256:
            return b"\x07"
        return b"\x03"


class ActionTap(ActionSequence):

    tag = "tap"

    def serialize_prefix(self, kc):
        if kc >= 256:
            return b"\x05"
        return b"\x01"


class ActionDelay(BasicAction):

    tag = "delay"

    def __init__(self, delay=0):
        super().__init__()
        self.delay = delay

    def serialize(self, vial_protocol):
        if vial_protocol < VIAL_PROTOCOL_ADVANCED_MACROS:
            raise RuntimeError("ActionDelay can only be used with vial_protocol>=2")
        delay = self.delay
        return struct.pack("BBBB", SS_QMK_PREFIX, SS_DELAY_CODE, (delay % 255) + 1, (delay // 255) + 1)

    def save(self):
        return super().save() + [self.delay]

    def restore(self, act):
        super().restore(act)
        self.delay = act[1]

    def __eq__(self, other):
        return super().__eq__(other) and self.delay == other.delay


class ActionPassword(BasicAction):
    """
    Password macro action that stores encrypted passwords.

    Passwords are encrypted with the master password key and stored
    in EEPROM. They are only decrypted when the user unlocks the
    password session in the GUI.
    """

    tag = "password"

    def __init__(self, encrypted_data=b"", salt=b"", iv=b""):
        super().__init__()
        self.encrypted_data = encrypted_data
        self.salt = salt
        self.iv = iv
        self._decrypted_text = None  # Cached plaintext (only in RAM)

    def serialize(self, vial_protocol):
        """
        Serialize for EEPROM storage.

        Format: SS_QMK_PREFIX + SS_PASSWORD_CODE + len_lo+1 + len_hi+1 + encrypted_data + iv(16)
        Note: Length bytes use +1 encoding to avoid 0x00 (NUL is macro separator).
        Note: Salt is stored separately in keyboard NVM, not per-macro.
        """
        from protocol.constants import VIAL_PROTOCOL_PASSWORD_MACROS
        if vial_protocol < VIAL_PROTOCOL_PASSWORD_MACROS:
            raise RuntimeError("ActionPassword requires vial_protocol >= 7")

        cipher_len = len(self.encrypted_data)
        if cipher_len > 65534:  # Max 65534 because we add 1 to each byte
            raise RuntimeError("Password data too large")

        # Encode length with +1 to avoid 0x00 bytes (like delay encoding)
        len_lo = (cipher_len & 0xFF) + 1
        len_hi = ((cipher_len >> 8) & 0xFF) + 1

        print("[PWD] ActionPassword.serialize: cipher_len={}, iv_len={}".format(cipher_len, len(self.iv)))
        print("[PWD]   encrypted[0:4]={}, iv[0:4]={}".format(
            self.encrypted_data[0:4].hex() if self.encrypted_data else "empty",
            self.iv[0:4].hex() if self.iv else "empty"))

        # Format: [prefix][code][len_lo+1][len_hi+1][data][iv]
        return struct.pack("BBBB", SS_QMK_PREFIX, SS_PASSWORD_CODE,
                           len_lo, len_hi) + self.encrypted_data + self.iv

    def save(self):
        """Save encrypted form (for .vil files)."""
        return [
            self.tag,
            base64.b64encode(self.encrypted_data).decode("ascii"),
            base64.b64encode(self.salt).decode("ascii"),
            base64.b64encode(self.iv).decode("ascii")
        ]

    def restore(self, act):
        """Restore from saved format."""
        super().restore(act)
        self.encrypted_data = base64.b64decode(act[1])
        self.salt = base64.b64decode(act[2])
        self.iv = base64.b64decode(act[3])

    def __eq__(self, other):
        return (super().__eq__(other) and
                self.encrypted_data == other.encrypted_data and
                self.salt == other.salt and
                self.iv == other.iv)

    def __repr__(self):
        return "{}<encrypted:{} bytes>".format(self.tag, len(self.encrypted_data))
