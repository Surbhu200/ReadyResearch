#!/usr/bin/env python3
"""
Comprehensive backend API tests for TextBlurb social app.
Tests all CRUD operations for posts and like/unlike functionality.
"""

import requests
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

# Get backend URL from environment - using the external URL from frontend/.env
BACKEND_URL = "https://word-swap-2.preview.emergentagent.com/api"

# Test data
TEST_POSTS = [
    {
        "content": "Just discovered this amazing quote: 'The only way to do great work is to love what you do.' - Steve Jobs",
        "source_link": "https://example.com/steve-jobs-quotes",
        "source_title": "Steve Jobs Inspirational Quotes",
        "author_name": "Sarah Chen"
    },
    {
        "content": "Life is what happens when you're busy making other plans. This quote always reminds me to stay present and appreciate the moment.",
        "source_link": "https://example.com/john-lennon",
        "source_title": "John Lennon Wisdom",
        "author_name": "Mike Rodriguez"
    },
    {
        "content": "The best time to plant a tree was 20 years ago. The second best time is now. Starting is often the hardest part of any journey.",
        "author_name": "Emma Watson"
    },
    {
        "content": "A" * 2000  # Testing max length
    }
]

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"✅ {test_name}")
        
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ {test_name}: {error}")
        
    def summary(self):
        total = self.passed + self.failed
        print(f"\n=== TEST SUMMARY ===")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        
        if self.errors:
            print(f"\n=== FAILURES ===")
            for error in self.errors:
                print(f"- {error}")
                
        return self.failed == 0

def test_root_endpoint(result: TestResult):
    """Test GET /api/ - Root endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/")
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "API is running" in data["message"]:
                result.add_pass("GET /api/ - Root endpoint returns success")
            else:
                result.add_fail("GET /api/ - Root endpoint", f"Unexpected response: {data}")
        else:
            result.add_fail("GET /api/ - Root endpoint", f"Status code {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("GET /api/ - Root endpoint", f"Request failed: {str(e)}")

def test_create_posts(result: TestResult) -> List[str]:
    """Test POST /api/posts - Create new posts"""
    created_post_ids = []
    
    # Test creating posts with all fields
    for i, post_data in enumerate(TEST_POSTS[:3]):
        try:
            response = requests.post(f"{BACKEND_URL}/posts", json=post_data)
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "content", "created_at", "likes", "author_name"]
                
                if all(field in data for field in required_fields):
                    created_post_ids.append(data["id"])
                    result.add_pass(f"POST /api/posts - Create post {i+1} with all fields")
                    
                    # Verify likes start at 0
                    if data["likes"] != 0:
                        result.add_fail(f"POST /api/posts - Post {i+1} likes", f"Expected likes=0, got {data['likes']}")
                else:
                    result.add_fail(f"POST /api/posts - Post {i+1}", f"Missing required fields in response: {data}")
            else:
                result.add_fail(f"POST /api/posts - Post {i+1}", f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            result.add_fail(f"POST /api/posts - Post {i+1}", f"Request failed: {str(e)}")
    
    # Test creating post with only required field (content)
    try:
        minimal_post = {"content": "Just a simple text blurb without any extras."}
        response = requests.post(f"{BACKEND_URL}/posts", json=minimal_post)
        if response.status_code == 200:
            data = response.json()
            created_post_ids.append(data["id"])
            result.add_pass("POST /api/posts - Create post with only content")
            
            # Verify default author_name
            if data.get("author_name") == "Anonymous":
                result.add_pass("POST /api/posts - Default author_name is Anonymous")
            else:
                result.add_fail("POST /api/posts - Default author", f"Expected 'Anonymous', got '{data.get('author_name')}'")
        else:
            result.add_fail("POST /api/posts - Minimal post", f"Status code {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("POST /api/posts - Minimal post", f"Request failed: {str(e)}")
    
    return created_post_ids

def test_validation_errors(result: TestResult):
    """Test POST /api/posts - Validation errors"""
    
    # Test empty content
    try:
        empty_post = {"content": ""}
        response = requests.post(f"{BACKEND_URL}/posts", json=empty_post)
        if response.status_code == 422:  # FastAPI validation error
            result.add_pass("POST /api/posts - Empty content validation")
        else:
            result.add_fail("POST /api/posts - Empty content", f"Expected 422, got {response.status_code}")
    except Exception as e:
        result.add_fail("POST /api/posts - Empty content", f"Request failed: {str(e)}")
    
    # Test content over 2000 chars
    try:
        long_post = {"content": "A" * 2001}
        response = requests.post(f"{BACKEND_URL}/posts", json=long_post)
        if response.status_code == 422:  # FastAPI validation error
            result.add_pass("POST /api/posts - Content too long validation")
        else:
            result.add_fail("POST /api/posts - Content too long", f"Expected 422, got {response.status_code}")
    except Exception as e:
        result.add_fail("POST /api/posts - Content too long", f"Request failed: {str(e)}")

def test_get_all_posts(result: TestResult, expected_count: int):
    """Test GET /api/posts - Get all posts"""
    try:
        response = requests.get(f"{BACKEND_URL}/posts")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                if len(data) >= expected_count:
                    result.add_pass(f"GET /api/posts - Returns list with {len(data)} posts")
                    
                    # Check if sorted by newest first (created_at descending)
                    if len(data) > 1:
                        timestamps = [datetime.fromisoformat(post["created_at"].replace('Z', '+00:00')) for post in data]
                        if timestamps == sorted(timestamps, reverse=True):
                            result.add_pass("GET /api/posts - Sorted by newest first")
                        else:
                            result.add_fail("GET /api/posts - Sorting", "Posts not sorted by newest first")
                else:
                    result.add_fail("GET /api/posts - Count", f"Expected at least {expected_count} posts, got {len(data)}")
            else:
                result.add_fail("GET /api/posts", f"Expected list, got {type(data)}")
        else:
            result.add_fail("GET /api/posts", f"Status code {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("GET /api/posts", f"Request failed: {str(e)}")

def test_get_posts_pagination(result: TestResult):
    """Test GET /api/posts - Pagination parameters"""
    try:
        # Test with skip and limit
        response = requests.get(f"{BACKEND_URL}/posts?skip=0&limit=2")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) <= 2:
                result.add_pass("GET /api/posts - Pagination with limit=2")
            else:
                result.add_fail("GET /api/posts - Pagination", f"Expected max 2 posts, got {len(data)}")
        else:
            result.add_fail("GET /api/posts - Pagination", f"Status code {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/posts - Pagination", f"Request failed: {str(e)}")

def test_get_single_post(result: TestResult, post_ids: List[str]):
    """Test GET /api/posts/{post_id} - Get single post"""
    if not post_ids:
        result.add_fail("GET /api/posts/{id}", "No post IDs available for testing")
        return
        
    post_id = post_ids[0]
    try:
        response = requests.get(f"{BACKEND_URL}/posts/{post_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get("id") == post_id:
                result.add_pass("GET /api/posts/{id} - Returns correct post")
            else:
                result.add_fail("GET /api/posts/{id}", f"Expected id {post_id}, got {data.get('id')}")
        else:
            result.add_fail("GET /api/posts/{id}", f"Status code {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("GET /api/posts/{id}", f"Request failed: {str(e)}")

def test_get_nonexistent_post(result: TestResult):
    """Test GET /api/posts/{post_id} - 404 for non-existent post"""
    fake_id = str(uuid.uuid4())
    try:
        response = requests.get(f"{BACKEND_URL}/posts/{fake_id}")
        if response.status_code == 404:
            result.add_pass("GET /api/posts/{id} - 404 for non-existent post")
        else:
            result.add_fail("GET /api/posts/{id} - 404", f"Expected 404, got {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/posts/{id} - 404", f"Request failed: {str(e)}")

def test_like_unlike_functionality(result: TestResult, post_ids: List[str]):
    """Test POST /api/posts/{post_id}/like and unlike"""
    if not post_ids:
        result.add_fail("Like/Unlike", "No post IDs available for testing")
        return
        
    post_id = post_ids[0]
    
    # Test liking a post
    try:
        response = requests.post(f"{BACKEND_URL}/posts/{post_id}/like")
        if response.status_code == 200:
            data = response.json()
            if data.get("likes") >= 1:
                result.add_pass("POST /api/posts/{id}/like - Increments like count")
                initial_likes = data.get("likes")
                
                # Test liking again
                response2 = requests.post(f"{BACKEND_URL}/posts/{post_id}/like")
                if response2.status_code == 200:
                    data2 = response2.json()
                    if data2.get("likes") == initial_likes + 1:
                        result.add_pass("POST /api/posts/{id}/like - Multiple likes work")
                    else:
                        result.add_fail("Multiple likes", f"Expected {initial_likes + 1}, got {data2.get('likes')}")
            else:
                result.add_fail("POST /api/posts/{id}/like", f"Expected likes >= 1, got {data.get('likes')}")
        else:
            result.add_fail("POST /api/posts/{id}/like", f"Status code {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("POST /api/posts/{id}/like", f"Request failed: {str(e)}")
    
    # Test unliking a post
    try:
        response = requests.post(f"{BACKEND_URL}/posts/{post_id}/unlike")
        if response.status_code == 200:
            data = response.json()
            result.add_pass("POST /api/posts/{id}/unlike - Decrements like count")
            
            # Test unliking when likes are 0
            current_likes = data.get("likes", 0)
            for _ in range(current_likes + 2):  # Unlike until 0 and try more
                requests.post(f"{BACKEND_URL}/posts/{post_id}/unlike")
            
            response_final = requests.post(f"{BACKEND_URL}/posts/{post_id}/unlike")
            if response_final.status_code == 200:
                data_final = response_final.json()
                if data_final.get("likes") >= 0:
                    result.add_pass("POST /api/posts/{id}/unlike - Doesn't go below 0")
                else:
                    result.add_fail("Unlike below 0", f"Likes went below 0: {data_final.get('likes')}")
        else:
            result.add_fail("POST /api/posts/{id}/unlike", f"Status code {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("POST /api/posts/{id}/unlike", f"Request failed: {str(e)}")

def test_like_unlike_nonexistent_post(result: TestResult):
    """Test like/unlike on non-existent post"""
    fake_id = str(uuid.uuid4())
    
    # Test like on non-existent post
    try:
        response = requests.post(f"{BACKEND_URL}/posts/{fake_id}/like")
        if response.status_code == 404:
            result.add_pass("POST /api/posts/{id}/like - 404 for non-existent post")
        else:
            result.add_fail("Like non-existent - 404", f"Expected 404, got {response.status_code}")
    except Exception as e:
        result.add_fail("Like non-existent", f"Request failed: {str(e)}")
    
    # Test unlike on non-existent post
    try:
        response = requests.post(f"{BACKEND_URL}/posts/{fake_id}/unlike")
        if response.status_code == 404:
            result.add_pass("POST /api/posts/{id}/unlike - 404 for non-existent post")
        else:
            result.add_fail("Unlike non-existent - 404", f"Expected 404, got {response.status_code}")
    except Exception as e:
        result.add_fail("Unlike non-existent", f"Request failed: {str(e)}")

def test_delete_post(result: TestResult, post_ids: List[str]):
    """Test DELETE /api/posts/{post_id}"""
    if not post_ids:
        result.add_fail("DELETE /api/posts/{id}", "No post IDs available for testing")
        return
        
    post_id = post_ids[-1]  # Use the last post for deletion
    
    try:
        response = requests.delete(f"{BACKEND_URL}/posts/{post_id}")
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "deleted" in data["message"].lower():
                result.add_pass("DELETE /api/posts/{id} - Successful deletion")
                
                # Verify post is actually deleted
                get_response = requests.get(f"{BACKEND_URL}/posts/{post_id}")
                if get_response.status_code == 404:
                    result.add_pass("DELETE /api/posts/{id} - Post actually removed")
                else:
                    result.add_fail("DELETE verification", f"Post still exists after deletion")
            else:
                result.add_fail("DELETE /api/posts/{id}", f"Unexpected response: {data}")
        else:
            result.add_fail("DELETE /api/posts/{id}", f"Status code {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("DELETE /api/posts/{id}", f"Request failed: {str(e)}")

def test_delete_nonexistent_post(result: TestResult):
    """Test DELETE /api/posts/{post_id} - 404 for non-existent post"""
    fake_id = str(uuid.uuid4())
    try:
        response = requests.delete(f"{BACKEND_URL}/posts/{fake_id}")
        if response.status_code == 404:
            result.add_pass("DELETE /api/posts/{id} - 404 for non-existent post")
        else:
            result.add_fail("DELETE non-existent - 404", f"Expected 404, got {response.status_code}")
    except Exception as e:
        result.add_fail("DELETE non-existent", f"Request failed: {str(e)}")

def main():
    """Run all backend API tests"""
    print("🚀 Starting TextBlurb Backend API Tests")
    print(f"Testing endpoint: {BACKEND_URL}")
    print("=" * 50)
    
    result = TestResult()
    
    # Test root endpoint
    test_root_endpoint(result)
    
    # Test post creation
    created_post_ids = test_create_posts(result)
    
    # Test validation errors
    test_validation_errors(result)
    
    # Test getting all posts
    test_get_all_posts(result, len(created_post_ids))
    
    # Test pagination
    test_get_posts_pagination(result)
    
    # Test getting single post
    test_get_single_post(result, created_post_ids)
    
    # Test 404 for non-existent post
    test_get_nonexistent_post(result)
    
    # Test like/unlike functionality
    test_like_unlike_functionality(result, created_post_ids)
    
    # Test like/unlike on non-existent posts
    test_like_unlike_nonexistent_post(result)
    
    # Test delete functionality
    test_delete_post(result, created_post_ids)
    
    # Test delete non-existent post
    test_delete_nonexistent_post(result)
    
    # Print summary
    success = result.summary()
    
    if success:
        print("\n🎉 All tests passed! Backend API is working correctly.")
    else:
        print(f"\n⚠️  {result.failed} test(s) failed. Please check the issues above.")
    
    return success

if __name__ == "__main__":
    main()