with open('/Users/dorianglon/Desktop/BPG_limited/Cornellians.txt', 'r') as f:
    lines = f.readlines()
    f.close()
    count = 0
    for line in lines:
        count += 1
    print('Current count in Cornellians.txt : ' + str(count))


with open('/Users/dorianglon/Desktop/BPG_limited/Cornellians_full_list.txt', 'r') as f:
    lines = f.readlines()
    f.close()
    count = 0
    for line in lines:
        count += 1
    print('Current count in Cornellians_full_list.txt : ' + str(count))
