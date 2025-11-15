import argparse

from .client import ScraperClient, logger
from .pipeline import (
    run_listings,
    run_act_pages,
    run_full_pipeline,
)
from .pdf_downloader import run_batch as run_download_batch
from .parse import run_parse_batch


def main():
    parser = argparse.ArgumentParser(prog="lawmate-indiacode", description="IndiaCode scraping pipeline")
    parser.add_argument(
        "mode",
        choices=["full", "listings", "acts", "download", "parse"],
        help="Which part of the pipeline to run",
    )
    parser.add_argument("--listing-rpp", type=int, default=1000)
    parser.add_argument("--listing-max-pages", type=int, default=1)
    parser.add_argument("--acts-batch", type=int, default=50)
    parser.add_argument("--download-batch", type=int, default=10)
    parser.add_argument("--parse-batch", type=int, default=10)

    args = parser.parse_args()
    client = ScraperClient()

    if args.mode == "full":
        run_full_pipeline(
            listing_rpp=args.listing_rpp,
            listing_max_pages=args.listing_max_pages,
            acts_batch_limit=args.acts_batch,
            download_batch_limit=args.download_batch,
            parse_batch_limit=args.parse_batch,
        )
    elif args.mode == "listings":
        logger.info("Running listings only")
        run_listings(client=client, rpp=args.listing_rpp, max_pages=args.listing_max_pages)
    elif args.mode == "acts":
        logger.info("Running act-page scraping batch")
        count = run_act_pages(client=client, batch_limit=args.acts_batch)
        logger.info("Scraped %d acts", count)
    elif args.mode == "download":
        logger.info("Running PDF download batch")
        count = run_download_batch(limit=args.download_batch)
        logger.info("Downloaded %d assets", count)
    elif args.mode == "parse":
        logger.info("Running parse batch")
        count = run_parse_batch(limit=args.parse_batch)
        logger.info("Parsed %d assets", count)


if __name__ == "__main__":
    main()