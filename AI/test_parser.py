from services.request_parser import parse_blood_request


# Test Case 1: English request
request1 = parse_blood_request(
    "Need 2 units B+ blood urgently at AIIMS Delhi"
)

print("\nTest Case 1:")
print(request1)


# Test Case 2: Emergency request
request2 = parse_blood_request(
    "Need 3 units O- blood immediately at Apollo Hospital"
)

print("\nTest Case 2:")
print(request2)


# Test Case 3: Missing information
request3 = parse_blood_request(
    "Need blood urgently"
)

print("\nTest Case 3:")
print(request3)


# Test Case 4: Hindi/Hinglish request
request4 = parse_blood_request(
    "Mujhe 2 units A+ khoon chahiye AIIMS Delhi mein"
)

print("\nTest Case 4:")
print(request4)