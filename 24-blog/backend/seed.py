"""
Blog Database Seeder
PostgreSQL ma'lumotlar bazasiga namunaviy kategoriyalar, mualliflar, maqolalar va izohlarni yuklash.
"""
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import SessionLocal, engine, Base
from app import models
from app.auth import hash_password

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("🌱 Seeding database...")

        # 1. Categories
        categories_data = [
            ("Business", "Global markets, finance, venture capital and economic insights."),
            ("Technology", "Artificial intelligence, software engineering, and modern tech trends."),
            ("Opinions", "Thought leadership, critical reviews, and editorial commentaries."),
            ("Culture", "Arts, literature, cinema, and modern societal narratives."),
            ("Travel", "Exploration, architecture, world heritage, and travel chronicles."),
            ("Books", "In-depth literary critique, book reviews, and author discussions.")
        ]

        cat_map = {}
        for name, desc in categories_data:
            cat = db.query(models.Category).filter(models.Category.name == name).first()
            if not cat:
                cat = models.Category(name=name, description=desc)
                db.add(cat)
                db.flush()
                print(f"  + Added category: {name}")
            cat_map[name] = cat

        # 2. Users
        users_data = [
            ("shamsiddin", "shamsiddin@example.com", "secret123"),
            ("sarah_connor", "sarah@haguemag.com", "writer123"),
            ("david_ross", "david@haguemag.com", "writer123"),
            ("elena_v", "elena@haguemag.com", "writer123"),
        ]

        user_map = {}
        for username, email, pwd in users_data:
            user = db.query(models.User).filter(models.User.email == email).first()
            if not user:
                user = models.User(
                    username=username,
                    email=email,
                    password=hash_password(pwd),
                    is_active=True
                )
                db.add(user)
                db.flush()
                print(f"  + Added user: {username} ({email})")
            user_map[username] = user

        # 3. Posts
        posts_data = [
            {
                "title": "The Global Shift: How Autonomous AI Systems Are Redefining Corporate Finance",
                "content": """Artificial intelligence is moving beyond generative experimentation into foundational algorithmic decision-making. In corporate finance and treasury operations, automated agent systems are now executing currency hedging, portfolio reallocation, and credit risk assessments in sub-second timeframes.

Financial institutions that previously relied on quarterly auditing cycles are pivoting to continuous real-time verification. While the efficiency gains are undeniable, regulatory authorities across Europe and North America are racing to institute safeguards against systemic algorithmic contagion. As capital allocation becomes increasingly automated, the premium on human strategic oversight has never been higher.""",
                "category": "Business",
                "author": "shamsiddin",
                "rating": 5
            },
            {
                "title": "The Architecture of Tomorrow: Building Sustainable Megacities in High-Heat Latitudes",
                "content": """Rapid urbanization across Central Asia, the Middle East, and North Africa is colliding with historic temperature records. Traditional glass curtain-wall skyscrapers act as greenhouse amplifiers, requiring tremendous kilowattage to cool. 

Modern structural architects are returning to biomimetic designs: passive wind towers, self-shading ceramic facades, and porous limestone composites. By integrating localized geothermal heat exchangers with smart district cooling grids, modern urban developments are demonstrating up to a 60 percent reduction in operational energy footprints. Sustainability is no longer an optional luxury—it is the baseline specification of survival.""",
                "category": "Travel",
                "author": "david_ross",
                "rating": 5
            },
            {
                "title": "Why Fast Software Engineering Demands Slow, Deliberate Architecture",
                "content": """The relentless pressure to ship features often leads to accumulated architectural friction. In software engineering, velocity is not measured by the lines of code committed per sprint, but by the sustainable rate of change a system can absorb without catastrophic failure.

Decoupling modules, enforcing strict schema contracts with tools like FastAPI and Pydantic, and relying on battle-tested relational storage engines like PostgreSQL creates enduring software foundations. When core domain abstractions are meticulously designed, subsequent feature iterations become trivial rather than hazardous.""",
                "category": "Technology",
                "author": "sarah_connor",
                "rating": 5
            },
            {
                "title": "Literary Realism in the Age of Synthetic Content: A Defense of Human Prose",
                "content": """As synthetic generative text floods the digital commons, the role of human literature shifts from mere content generation to visceral empathy and authentic truth-telling. The finest novels do not merely assemble plausible sentences; they capture the precise resonance of heartbreak, doubt, and triumphant grit.

Readers are displaying a renewed appetite for deeply textured, imperfect, and idiosyncratic voices. The tactile feel of print volumes and the patient cadences of literary essays are experiencing an unexpected renaissance among younger demographics seeking refuge from hyper-accelerated feeds.""",
                "category": "Books",
                "author": "elena_v",
                "rating": 4
            },
            {
                "title": "The Rebirth of Public Transit: High-Speed Rail Corridors Connecting Eurasia",
                "content": """Investments in electrified high-speed railways are transforming continental trade and mobility. High-capacity intercity rail lines are outpacing short-haul air routes in speed, convenience, and carbon efficiency.

From Tashkent and Samarkand to modern European transits, seamless passenger logistics is redefining regional tourism and commerce. Cities linked by rapid passenger networks function increasingly as interconnected economic super-clusters.""",
                "category": "Travel",
                "author": "shamsiddin",
                "rating": 5
            },
            {
                "title": "The Ethics of Open Model Weights: Power, Peril, and Scientific Sovereignty",
                "content": """The debate over open-source artificial intelligence models strikes at the heart of technological democracy. Restricting frontier models to a handful of monopolistic cloud platforms concentrates unprecedented cognitive leverage into private hands.

Conversely, open model weights enable independent security audits, academic verification, and localized sovereign applications adapted to specific cultures and languages. The future of equitable innovation rests on preserving accessible open ecosystems.""",
                "category": "Opinions",
                "author": "sarah_connor",
                "rating": 5
            }
        ]

        post_map = {}
        for p in posts_data:
            existing = db.query(models.Post).filter(models.Post.title == p["title"]).first()
            if not existing:
                post = models.Post(
                    title=p["title"],
                    content=p["content"],
                    published=True,
                    rating=p["rating"],
                    owner_id=user_map[p["author"]].id,
                    category_id=cat_map[p["category"]].id
                )
                db.add(post)
                db.flush()
                print(f"  + Added post: {p['title'][:40]}...")
                post_map[p["title"]] = post
            else:
                post_map[p["title"]] = existing

        # 4. Comments
        sample_comments = [
            ("The Global Shift: How Autonomous AI Systems Are Redefining Corporate Finance", "david_ross", "Fascinating analysis. The section on systemic algorithmic contagion is spot on."),
            ("The Global Shift: How Autonomous AI Systems Are Redefining Corporate Finance", "sarah_connor", "We're already observing this shift in institutional trading desks."),
            ("Why Fast Software Engineering Demands Slow, Deliberate Architecture", "shamsiddin", "FastAPI and PostgreSQL are indeed the gold standard for reliable backend engineering."),
            ("Why Fast Software Engineering Demands Slow, Deliberate Architecture", "elena_v", "Clean domain architecture always pays compound interest in the long run.")
        ]

        for post_title, username, comment_text in sample_comments:
            if post_title in post_map and username in user_map:
                pst = post_map[post_title]
                usr = user_map[username]
                existing_c = db.query(models.Comment).filter(
                    models.Comment.post_id == pst.id,
                    models.Comment.user_id == usr.id,
                    models.Comment.content == comment_text
                ).first()
                if not existing_c:
                    c = models.Comment(
                        content=comment_text,
                        post_id=pst.id,
                        user_id=usr.id
                    )
                    db.add(c)
                    print(f"  + Added comment by {username} on post #{pst.id}")

        db.commit()
        print("✅ Database seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
