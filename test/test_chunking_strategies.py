"""
测试三种分块策略的效果
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.schema import Document
from app.utils.chunkers import FixedChunker, SemanticChunker, SentenceChunker, get_chunker


def print_chunks(chunks, strategy_name):
    """打印分块结果"""
    print(f"\n{'='*60}")
    print(f"策略: {strategy_name}")
    print(f"分块数量: {len(chunks)}")
    print(f"{'='*60}")
    
    for i, chunk in enumerate(chunks):
        content = chunk.page_content
        print(f"\n--- 分块 {i+1} (长度: {len(content)}) ---")
        if len(content) > 200:
            print(f"{content[:100]}...{content[-100:]}")
        else:
            print(content)


def test_fixed_chunker():
    """测试固定长度分块"""
    print("\n" + "="*60)
    print("测试固定长度分块策略")
    print("="*60)
    
    text = """
人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。

人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大，可以设想，未来人工智能带来的科技产品，将会是人类智慧的"容器"。人工智能可以对人的意识、思维的信息过程进行模拟。人工智能不是人的智能，但能像人那样思考，也可能超过人的智能。

机器学习是人工智能的一个重要分支。它是一门多领域交叉学科，涉及概率论、统计学、逼近论、凸分析、计算复杂性理论等多门学科。专门研究计算机怎样模拟或实现人类的学习行为，以获取新的知识或技能，重新组织已有的知识结构使之不断改善自身的性能。

深度学习是机器学习的分支，是一种以人工神经网络为架构，对数据进行表征学习的算法。深度学习的概念源于人工神经网络的研究，含多隐层的多层感知器就是一种深度学习结构。深度学习通过组合低层特征形成更加抽象的高层表示属性类别或特征，以发现数据的分布式特征表示。
"""
    
    doc = Document(page_content=text.strip(), metadata={"source": "test"})
    
    chunker = FixedChunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.split([doc])
    
    print_chunks(chunks, "固定长度分块 (chunk_size=200, overlap=50)")
    
    chunker2 = FixedChunker(chunk_size=500, chunk_overlap=100)
    chunks2 = chunker2.split([doc])
    
    print_chunks(chunks2, "固定长度分块 (chunk_size=500, overlap=100)")


def test_sentence_chunker():
    """测试句子分块"""
    print("\n" + "="*60)
    print("测试句子分块策略")
    print("="*60)
    
    text = """
人工智能是计算机科学的一个分支。它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器！该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。

人工智能从诞生以来，理论和技术日益成熟。应用领域也不断扩大，可以设想，未来人工智能带来的科技产品，将会是人类智慧的"容器"。人工智能不是人的智能，但能像人那样思考，也可能超过人的智能？

机器学习是人工智能的一个重要分支。它是一门多领域交叉学科，涉及概率论、统计学、逼近论、凸分析、计算复杂性理论等多门学科。专门研究计算机怎样模拟或实现人类的学习行为，以获取新的知识或技能，重新组织已有的知识结构使之不断改善自身的性能。

深度学习是机器学习的分支，是一种以人工神经网络为架构，对数据进行表征学习的算法。深度学习的概念源于人工神经网络的研究，含多隐层的多层感知器就是一种深度学习结构。深度学习通过组合低层特征形成更加抽象的高层表示属性类别或特征，以发现数据的分布式特征表示。
"""
    
    doc = Document(page_content=text.strip(), metadata={"source": "test"})
    
    chunker = SentenceChunker(chunk_size=150, chunk_overlap=30)
    chunks = chunker.split([doc])
    
    print_chunks(chunks, "句子分块 (chunk_size=150, overlap=30)")
    
    chunker2 = SentenceChunker(chunk_size=300, chunk_overlap=50)
    chunks2 = chunker2.split([doc])
    
    print_chunks(chunks, "句子分块 (chunk_size=300, overlap=50)")


def test_semantic_chunker():
    """测试语义分块"""
    print("\n" + "="*60)
    print("测试语义分块策略")
    print("="*60)
    
    text = """
人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。

人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大，可以设想，未来人工智能带来的科技产品，将会是人类智慧的"容器"。人工智能不是人的智能，但能像人那样思考，也可能超过人的智能。

机器学习是人工智能的一个重要分支。它是一门多领域交叉学科，涉及概率论、统计学、逼近论、凸分析、计算复杂性理论等多门学科。专门研究计算机怎样模拟或实现人类的学习行为，以获取新的知识或技能，重新组织已有的知识结构使之不断改善自身的性能。

深度学习是机器学习的分支，是一种以人工神经网络为架构，对数据进行表征学习的算法。深度学习的概念源于人工神经网络的研究，含多隐层的多层感知器就是一种深度学习结构。深度学习通过组合低层特征形成更加抽象的高层表示属性类别或特征，以发现数据的分布式特征表示。

自然语言处理是人工智能和语言学领域的分支学科。在这一领域中探讨如何处理及运用自然语言。自然语言处理包括多方面和步骤，基本有认知、理解、生成等部分。

计算机视觉是一门研究如何使机器"看"的科学，更进一步的说，就是是指用摄影机和电脑代替人眼对目标进行识别、跟踪和测量等机器视觉，并进一步做图形处理，使电脑处理成为更适合人眼观察或传送给仪器检测的图像。
"""
    
    doc = Document(page_content=text.strip(), metadata={"source": "test"})
    
    print("\n注意: 语义分块需要嵌入模型支持，如果没有配置可能会回退到固定分块")
    
    try:
        chunker = SemanticChunker(chunk_size=500, chunk_overlap=100)
        chunks = chunker.split([doc])
        print_chunks(chunks, "语义分块 (需要嵌入模型)")
    except Exception as e:
        print(f"\n语义分块测试失败: {str(e)}")
        print("这通常是因为没有配置嵌入模型，语义分块会回退到固定分块")


def test_get_chunker():
    """测试 get_chunker 工厂函数"""
    print("\n" + "="*60)
    print("测试 get_chunker 工厂函数")
    print("="*60)
    
    text = "这是一个测试文本。用于验证分块器工厂函数是否正常工作。"
    doc = Document(page_content=text, metadata={"source": "test"})
    
    for strategy in ['fixed', 'semantic', 'sentence']:
        chunker = get_chunker(strategy, chunk_size=100, chunk_overlap=20)
        chunks = chunker.split([doc])
        print(f"\n策略 '{strategy}' -> 分块器类型: {type(chunker).__name__}")
        print(f"分块数量: {len(chunks)}")


def test_document_loader():
    """测试 document_loader 中的 split_document_with_strategy 函数"""
    print("\n" + "="*60)
    print("测试 split_document_with_strategy 函数")
    print("="*60)
    
    from app.utils.document_loader import split_document_with_strategy
    
    text = """
知识库是一种用于存储和组织知识的系统。它可以帮助用户快速查找和获取所需的信息。知识库通常包含结构化和非结构化的数据，如文档、文章、问答对等。

在人工智能领域，知识库被广泛应用于问答系统、推荐系统和智能助手等场景。通过将知识库与大语言模型结合，可以实现更加智能和准确的问答服务。

向量数据库是知识库的重要组成部分。它可以将文本转换为向量表示，并支持高效的相似度搜索。常用的向量数据库包括 Pinecone、Weaviate、Milvus 等。
"""
    
    docs = [Document(page_content=text.strip(), metadata={"source": "test"})]
    
    for strategy in ['fixed', 'sentence']:
        chunks = split_document_with_strategy(
            docs=docs,
            strategy=strategy,
            chunk_size=200,
            chunk_overlap=50
        )
        print(f"\n策略: {strategy}, 分块数量: {len(chunks)}")


def compare_strategies():
    """比较三种策略的分块效果"""
    print("\n" + "="*60)
    print("比较三种分块策略")
    print("="*60)
    
    text = """
Python是一种广泛使用的高级编程语言，由Guido van Rossum于1991年首次发布。Python的设计哲学强调代码的可读性和简洁性，它的语法允许程序员用更少的代码行表达概念。

Python支持多种编程范式，包括面向对象、命令式、函数式和过程式编程。它具有一个全面的标准库，并且可以轻松地与其他语言（如C/C++）集成。

Python在数据科学、机器学习、Web开发、自动化脚本等领域都有广泛应用。流行的Python库包括NumPy、Pandas、TensorFlow、PyTorch、Django和Flask等。

Python的简洁语法和丰富的生态系统使其成为初学者和专业开发者的首选语言之一。它的社区活跃，有大量的开源项目和文档可供参考。
"""
    
    doc = Document(page_content=text.strip(), metadata={"source": "test"})
    
    chunk_size = 200
    chunk_overlap = 50
    
    print(f"\n参数: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    print("-" * 60)
    
    strategies = ['fixed', 'sentence']
    
    for strategy in strategies:
        chunker = get_chunker(strategy, chunk_size, chunk_overlap)
        chunks = chunker.split([doc])
        
        total_chars = sum(len(c.page_content) for c in chunks)
        avg_chars = total_chars / len(chunks) if chunks else 0
        
        print(f"\n策略: {strategy}")
        print(f"  - 分块数量: {len(chunks)}")
        print(f"  - 平均分块长度: {avg_chars:.1f} 字符")
        print(f"  - 总字符数: {total_chars}")


def main():
    """主测试函数"""
    print("="*60)
    print("分块策略测试脚本")
    print("="*60)
    
    test_fixed_chunker()
    test_sentence_chunker()
    test_semantic_chunker()
    test_get_chunker()
    test_document_loader()
    compare_strategies()
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)


if __name__ == "__main__":
    main()
