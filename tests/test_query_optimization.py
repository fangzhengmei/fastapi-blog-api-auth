import pytest
from sqlalchemy import event
from blog import models
from blog.repository import blog as blog_repository
from blog.repository import tag as tag_repository


class QueryCounter:
    def __init__(self, db_engine):
        self.db_engine = db_engine
        self.query_count = 0
        self.queries = []

    def __enter__(self):
        self.query_count = 0
        self.queries = []
        
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            stmt_upper = statement.strip().upper()
            if stmt_upper.startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE')):
                if not stmt_upper.startswith(('SELECT 1', 'PRAGMA', 'ROLLBACK', 'COMMIT', 'BEGIN')):
                    self.query_count += 1
                    self.queries.append(statement[:150])
        
        event.listen(self.db_engine, 'before_cursor_execute', before_cursor_execute)
        self.listener = before_cursor_execute
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        event.remove(self.db_engine, 'before_cursor_execute', self.listener)


class TestBlogQueryOptimization:
    def test_get_all_blogs_no_n_plus_one(self, test_db, test_user, test_db_engine):
        small_count = 2
        for i in range(small_count):
            blog = models.Blog(
                title=f"Blog {i}",
                body=f"Content {i}",
                user_id=test_user.id
            )
            tag1 = models.Tag(
                name=f"Tag{i}a",
                slug=f"tag{i}a"
            )
            blog.tags = [tag1]
            test_db.add(blog)
        test_db.commit()
        
        test_db.expire_all()
        
        with QueryCounter(test_db_engine) as counter_small:
            result_small = blog_repository.get_all(test_db, page=1, per_page=10)
        
        queries_small = counter_small.query_count
        print(f"\n=== Small dataset ({small_count} blogs) queries: {queries_small} ===")
        for q in counter_small.queries:
            print(f"  - {q}...")
        
        test_db.expire_all()
        
        large_count = 10
        for i in range(small_count, small_count + large_count):
            blog = models.Blog(
                title=f"Blog {i}",
                body=f"Content {i}",
                user_id=test_user.id
            )
            tag1 = models.Tag(
                name=f"Tag{i}a",
                slug=f"tag{i}a"
            )
            tag2 = models.Tag(
                name=f"Tag{i}b",
                slug=f"tag{i}b"
            )
            blog.tags = [tag1, tag2]
            test_db.add(blog)
        test_db.commit()
        
        test_db.expire_all()
        
        with QueryCounter(test_db_engine) as counter_large:
            result_large = blog_repository.get_all(test_db, page=1, per_page=100)
        
        queries_large = counter_large.query_count
        print(f"\n=== Large dataset ({small_count + large_count} blogs) queries: {queries_large} ===")
        for q in counter_large.queries:
            print(f"  - {q}...")
        
        assert result_small['total'] == small_count
        assert result_large['total'] == small_count + large_count
        
        assert queries_large == queries_small, (
            f"N+1 Problem Detected!\n"
            f"With {small_count} blogs: {queries_small} queries\n"
            f"With {small_count + large_count} blogs: {queries_large} queries\n"
            f"Query count increased with data volume - N+1 loading detected!\n"
            f"Check that selectinload is being used for Blog.tags and Blog.creator"
        )
        
        for blog in result_large['items']:
            assert len(blog.tags) > 0
            assert blog.creator is not None
            assert blog.creator.name == test_user.name
        
        print(f"\n=== SUCCESS: Query count is constant ({queries_large}) regardless of data size ===")

    def test_get_blog_by_id_no_n_plus_one(self, test_db, test_user, test_tag, test_tag2, test_db_engine):
        blog = models.Blog(
            title="Test Blog",
            body="Test Content",
            user_id=test_user.id
        )
        blog.tags = [test_tag, test_tag2]
        test_db.add(blog)
        test_db.commit()
        blog_id = blog.id
        
        test_db.expire_all()
        
        with QueryCounter(test_db_engine) as counter:
            result = blog_repository.show(blog_id, test_db)
        
        print(f"\n=== show blog queries ({counter.query_count}): ===")
        for q in counter.queries:
            print(f"  - {q}...")
        
        assert result.id == blog_id
        assert len(result.tags) == 2
        assert result.creator is not None
        
        max_expected_queries = 5
        assert counter.query_count <= max_expected_queries, (
            f"Too many queries ({counter.query_count} > {max_expected_queries}). "
            f"Check selectinload usage.\n"
            f"Queries: {counter.queries}"
        )

    def test_filter_blogs_by_tag_no_n_plus_one(self, test_db, test_user, test_db_engine):
        tag1 = models.Tag(name="Tag1", slug="tag1")
        tag2 = models.Tag(name="Tag2", slug="tag2")
        test_db.add_all([tag1, tag2])
        test_db.commit()
        tag1_id = tag1.id
        
        small_blog_count = 2
        for i in range(small_blog_count):
            blog = models.Blog(
                title=f"Blog {i}",
                body=f"Content {i}",
                user_id=test_user.id
            )
            blog.tags = [tag1]
            test_db.add(blog)
        test_db.commit()
        
        test_db.expire_all()
        
        with QueryCounter(test_db_engine) as counter_small:
            result_small = blog_repository.get_all(
                test_db,
                page=1,
                per_page=10,
                tag_id=tag1_id
            )
        
        queries_small = counter_small.query_count
        print(f"\n=== Filter small dataset ({small_blog_count} blogs) queries: {queries_small} ===")
        
        test_db.expire_all()
        
        large_blog_count = 8
        for i in range(small_blog_count, small_blog_count + large_blog_count):
            blog = models.Blog(
                title=f"Blog {i}",
                body=f"Content {i}",
                user_id=test_user.id
            )
            if i < small_blog_count + 5:
                blog.tags = [tag1]
            blog.tags.append(tag2)
            test_db.add(blog)
        test_db.commit()
        
        test_db.expire_all()
        
        with QueryCounter(test_db_engine) as counter_large:
            result_large = blog_repository.get_all(
                test_db,
                page=1,
                per_page=100,
                tag_id=tag1_id
            )
        
        queries_large = counter_large.query_count
        print(f"\n=== Filter large dataset (more blogs) queries: {queries_large} ===")
        
        assert result_small['total'] == small_blog_count
        assert result_large['total'] == small_blog_count + 5
        
        assert queries_large == queries_small, (
            f"N+1 Problem Detected in filtered query!\n"
            f"With {small_blog_count} blogs: {queries_small} queries\n"
            f"With more blogs: {queries_large} queries\n"
            f"Query count increased with data volume - N+1 loading detected!"
        )
        
        for blog in result_large['items']:
            tag_names = {t.name for t in blog.tags}
            assert "Tag1" in tag_names
            assert blog.creator is not None


class TestGetBlogsByTagOptimization:
    def test_get_blogs_by_tag_no_n_plus_one(self, test_db, test_user, test_db_engine):
        tag = models.Tag(
            name="TestTag",
            slug="testtag"
        )
        test_db.add(tag)
        test_db.commit()
        test_db.refresh(tag)
        tag_id = tag.id
        
        small_count = 2
        for i in range(small_count):
            blog = models.Blog(
                title=f"Blog {i}",
                body=f"Content {i}",
                user_id=test_user.id
            )
            blog.tags = [tag]
            test_db.add(blog)
        test_db.commit()
        
        test_db.expire_all()
        
        with QueryCounter(test_db_engine) as counter_small:
            result_small = tag_repository.get_blogs_by_tag(
                tag_id=tag_id, 
                db=test_db, 
                page=1, 
                per_page=10
            )
        
        queries_small = counter_small.query_count
        print(f"\n=== get_blogs_by_tag small dataset queries: {queries_small} ===")
        
        test_db.expire_all()
        
        large_count = 8
        for i in range(small_count, small_count + large_count):
            blog = models.Blog(
                title=f"Blog {i}",
                body=f"Content {i}",
                user_id=test_user.id
            )
            blog.tags = [tag]
            test_db.add(blog)
        test_db.commit()
        
        test_db.expire_all()
        
        with QueryCounter(test_db_engine) as counter_large:
            result_large = tag_repository.get_blogs_by_tag(
                tag_id=tag_id, 
                db=test_db, 
                page=1, 
                per_page=100
            )
        
        queries_large = counter_large.query_count
        print(f"\n=== get_blogs_by_tag large dataset queries: {queries_large} ===")
        
        assert result_small['total'] == small_count
        assert result_large['total'] == small_count + large_count
        
        assert queries_large == queries_small, (
            f"N+1 Problem Detected in get_blogs_by_tag!\n"
            f"With {small_count} blogs: {queries_small} queries\n"
            f"With {small_count + large_count} blogs: {queries_large} queries\n"
            f"Query count increased with data volume!"
        )
        
        for blog in result_large['blogs']:
            assert len(blog.tags) >= 1
            assert blog.creator is not None
