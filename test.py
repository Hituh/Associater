my_string = "hunter, warrior,mage, toolmaker"
my_array = my_string.split(",")

for i in range(len(my_array)):
    my_array[i] = my_array[i].replace(" ", "")
print(my_array)
