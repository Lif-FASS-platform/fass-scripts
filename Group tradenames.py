from collections import defaultdict
import json

root = r"C:\Users\clga\OneDrive - Netcompany\Desktop"


def group_level_two():
    filepath = rf"{root}\all tradenames.txt"
    group_map = dict()
    with open(filepath, "r", encoding="utf-8") as f:
        list_of_tradenames = f.readlines()
        list_of_tradenames.sort()
        # print(list_of_tradenames[:5])
        for tradename in list_of_tradenames:
            first = tradename[:1].lower().capitalize()
            two_first = tradename[:2].lower().capitalize()

            if first not in group_map:
                group_map[first] = defaultdict(int)
            else:
                group_map[first][two_first] += 1

        print(json.dumps(group_map, sort_keys=True, indent=4))


def group_level_three():
    filepath = rf"{root}\all tradenames.txt"
    res = dict()
    with open(filepath, "r", encoding="utf-8") as f:
        list_of_tradenames = f.readlines()
        list_of_tradenames.sort()
        # print(list_of_tradenames[:5])

        for tradename in list_of_tradenames:
            ch1 = tradename[:1].lower().capitalize()
            ch2 = tradename[:2].lower().capitalize()
            ch3 = tradename[:3].lower().capitalize()

            if ch1 not in res:
                res[ch1] = dict()
                res[ch1]["count"] = 1
                res[ch1]["subgroups"] = dict()
                res[ch1]["subgroups"][ch2] = dict()
                res[ch1]["subgroups"][ch2]["count"] = 1
                res[ch1]["subgroups"][ch2]["subgroups"] = dict()
                res[ch1]["subgroups"][ch2]["subgroups"][ch3] = 1
            else:
                res[ch1]["count"] += 1
                if ch2 not in res[ch1]["subgroups"]:
                    res[ch1]["subgroups"][ch2] = dict()
                    res[ch1]["subgroups"][ch2]["count"] = 1
                    res[ch1]["subgroups"][ch2]["subgroups"] = dict()
                    res[ch1]["subgroups"][ch2]["subgroups"][ch3] = 1
                else:
                    res[ch1]["subgroups"][ch2]["count"] += 1
                    if ch3 not in res[ch1]["subgroups"][ch2]["subgroups"]:
                        res[ch1]["subgroups"][ch2]["subgroups"][ch3] = 1
                    else:
                        res[ch1]["subgroups"][ch2]["subgroups"][ch3] += 1

    jdump = json.dumps(res, sort_keys=True, indent=4)
    path_out = rf"{root}\tradenamegroups.txt"
    with open(path_out, "w") as output:
        print(jdump, file=output)


def group_flat_level_three():
    filepath = rf"{root}\all tradenames.txt"
    res = dict()
    with open(filepath, "r", encoding="utf-8") as f:
        list_of_tradenames = f.readlines()
        list_of_tradenames.sort()
        # print(list_of_tradenames[:5])

        for tradename in list_of_tradenames:
            ch1 = tradename[:1].lower().capitalize()
            ch3 = tradename[:3].lower().capitalize()

            if ch1 not in res:
                res[ch1] = dict()
                res[ch1]["count"] = 1
                res[ch1]["subgroups"] = dict()
                res[ch1]["subgroups"][ch3] = 1
            else:
                res[ch1]["count"] += 1
                # res[ch1]["subgroups"][ch2]["count"] += 1
                if ch3 not in res[ch1]["subgroups"]:
                    res[ch1]["subgroups"][ch3] = 1
                else:
                    res[ch1]["subgroups"][ch3] += 1

    jdump = json.dumps(res, sort_keys=True, indent=4)
    path_out = rf"{root}\tradenamegroups_2.txt"
    with open(path_out, "w") as output:
        print(jdump, file=output)


def collate_group(min_group_size: int, subgroup: dict):
    res = subgroup
    list_of_ch = list(subgroup.keys())

    i = 0
    while min(subgroup.values()) <= min_group_size and len(list_of_ch) > 1:
        if i == len(list_of_ch):
            i = 0

        ch = list_of_ch[i]
        count = subgroup[ch]
        if count > min_group_size:
            i += 1
            continue

        if i + 1 < len(list_of_ch):
            next_ch = list_of_ch.pop(i + 1)
            next_ch_count = res.pop(next_ch)
            res[ch] += next_ch_count
        else:
            prev_ch = list_of_ch[i - 1]
            res[prev_ch] += res.pop(ch)

    # print(res)
    return res


def group_by_size():
    min_group_size = 90
    filepath = rf"{root}\tradenamegroups_2.txt"
    # res = dict()
    with open(filepath, "r", encoding="utf-8") as f:
        grouped_tradenames = json.loads(f.read())

    res = grouped_tradenames
    for ch1, v1 in grouped_tradenames.items():
        # for ch2, v2 in v1["subgroups"].items():
        subgroup = collate_group(min_group_size, v1["subgroups"])
        res[ch1]["subgroups"] = subgroup

    jdump = json.dumps(res, sort_keys=True, indent=4)

    path_out = rf"{root}\smart_tradename_group.txt"
    with open(path_out, "w", encoding="utf-8") as output:
        print(jdump, file=output)


if __name__ == "__main__":
    # group_level_two()
    # group_level_three()
    group_flat_level_three()
    group_by_size()
